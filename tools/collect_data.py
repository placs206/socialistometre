#!/usr/bin/env python3
"""Collecte des données brutes du Socialistomètre (V1).

Télécharge les séries depuis les API/fichiers institutionnels listés dans config/sources.json,
les enregistre TELLES QUELLES dans data/raw/ et écrit data/raw/MANIFEST.json
(URL, date de collecte, octets, SHA-256, statut HTTP).

Aucune transformation ici. Aucune donnée n'est fabriquée ni substituée.
Usage : python3 tools/collect_data.py [--date AAAA-MM-JJ]
"""
import hashlib, json, os, sys, time, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
UA = {"User-Agent": "socialistometre-collector/1.0 (recherche; contact: depot GitHub du projet)"}

WB_INDICATORS = [  # (code, source_id WB, fichier)
    ("TM.TAX.MRCH.SM.AR.ZS", 2), ("TM.TAX.MRCH.WM.AR.ZS", 2),
    ("GC.REV.SOCL.ZS", 2), ("SE.PRM.PRIV.ZS", 2), ("SE.SEC.PRIV.ZS", 2),
    ("NE.CON.GOVT.ZS", 2),
    ("GOV_WGI_VA.EST", 3), ("GOV_WGI_RL.EST", 3), ("GOV_WGI_RQ.EST", 3),
]
OECD_H = {"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}
OECD = [  # (fichier, dataflow)
    ("oecd_cit.csv", "OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0"),
    ("oecd_pit_top.csv", "OECD.CTP.TPS,DSD_TAX_PIT@DF_PIT_TOP_EARN_THRESH,1.0"),
    ("oecd_pmr.csv", "OECD.ECO.GCRD,DSD_PMR@DF_PMR,1.4"),
    ("oecd_pmr_wbg.csv", "OECD.ECO.GCRD,DSD_PMR@DF_PMR_WBG,1.4"),
    ("oecd_min2ave.csv", "OECD.ELS.SAE,DSD_EARNINGS@MIN2AVE,1.0"),
]
# Ajouts V1.1 (prélèvements obligatoires, coin fiscal sur le travail)
OECD_V11 = [  # (fichier, dataflow, filtre sur les lignes conservées ou None)
    ("oecd_rev_global.csv", "OECD.CTP.TPS,DSD_REV_COMP_GLOBAL@DF_RSGLOBAL,1.0",
     lambda r: r["SECTOR"] == "S13" and r["UNIT_MEASURE"] == "PT_B1GQ" and r["STANDARD_REVENUE"] in ("_T", "T_1100", "T_2000", "T_3000")),
    ("oecd_tw_comp.csv", "OECD.CTP.TPS,DSD_TAX_WAGES_COMP@DF_TW_COMP,1.0", None),
]
FH_URL = "https://freedomhouse.org/sites/default/files/2024-02/All_data_FIW_2013-2024.xlsx"


def fetch(url, headers=None, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={**UA, **(headers or {})})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.status, r.read()
        except Exception as e:  # noqa
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"échec {url}: {last}")


def save(manifest, name, url, status, data, date, note=""):
    path = os.path.join(RAW, name)
    with open(path, "wb") as f:
        f.write(data)
    manifest[name] = {"url": url, "date_collecte": date, "http": status, "octets": len(data),
                      "sha256": hashlib.sha256(data).hexdigest(), "note": note}
    print(f"OK {name} ({len(data)} o)")


def ajout_v11(date):
    """Ajoute les fichiers V1.1 sans retélécharger les autres ; fusionne dans MANIFEST.json.
    Les lignes non utilisées de Global Revenue Statistics (28 Mo) sont écartées ; l'empreinte du fichier complet reçu est conservée."""
    import csv, io
    mpath = os.path.join(RAW, "MANIFEST.json")
    man = json.load(open(mpath, encoding="utf-8"))
    for fname, df, filt in OECD_V11:
        u = f"https://sdmx.oecd.org/public/rest/data/{df}/all?startPeriod=2019&dimensionAtObservation=AllDimensions"
        st, d = fetch(u, OECD_H)
        note = "OECD SDMX-CSV (startPeriod=2019)"
        if filt:
            rows = list(csv.DictReader(io.StringIO(d.decode("utf-8"))))
            keep = [r for r in rows if filt(r)]
            buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader(); w.writerows(keep)
            note += f" ; fichier complet reçu : {len(d)} octets, SHA-256 {hashlib.sha256(d).hexdigest()} ; conservé : {len(keep)}/{len(rows)} lignes (S13, % du PIB, codes _T, T_1100, T_2000, T_3000)"
            d = buf.getvalue().encode("utf-8")
        save(man["fichiers"], fname, u, st, d, date, note)
    man["genere_le"] = man["genere_le"]
    json.dump(man, open(mpath, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    date = time.strftime("%Y-%m-%d")
    if "--ajout-v1.1" in sys.argv:
        ajout_v11(sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else date)
        return
    if "--date" in sys.argv:
        date = sys.argv[sys.argv.index("--date") + 1]
    os.makedirs(RAW, exist_ok=True)
    manifest = {}

    # Banque mondiale : pays
    u = "https://api.worldbank.org/v2/country?format=json&per_page=400"
    st, d = fetch(u)
    save(manifest, "wb_countries.json", u, st, d, date, "Métadonnées pays WB (région, revenu, ISO3)")

    for code, src in WB_INDICATORS:
        pages, page = [], 1
        while True:
            u = (f"https://api.worldbank.org/v2/country/all/indicator/{code}"
                 f"?format=json&per_page=20000&date=2014:2025&source={src}&page={page}")
            st, d = fetch(u)
            j = json.loads(d)
            pages.append(j)
            if page >= j[0]["pages"]:
                break
            page += 1
        blob = json.dumps(pages, ensure_ascii=False).encode()
        save(manifest, f"wb_{code}.json", f"https://api.worldbank.org/v2/country/all/indicator/{code}?date=2014:2025&source={src}",
             200, blob, date, f"WB source {src}; {len(pages)} page(s) API concaténée(s)")

    for fname, df in OECD:
        u = f"https://sdmx.oecd.org/public/rest/data/{df}/all?startPeriod=2014&dimensionAtObservation=AllDimensions"
        st, d = fetch(u, OECD_H)
        save(manifest, fname, u, st, d, date, "OECD SDMX-CSV (startPeriod=2014)")

    st, d = fetch(FH_URL)
    save(manifest, "freedomhouse_fiw_2013-2024.xlsx", FH_URL, st, d, date,
         "Freedom House, Freedom in the World 2013-2024 (ONG ; édition 2024 = année civile 2023)")

    with open(os.path.join(RAW, "MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump({"genere_le": date, "fichiers": manifest}, f, ensure_ascii=False, indent=1)
    print("Manifeste écrit :", len(manifest), "fichiers")


if __name__ == "__main__":
    main()
