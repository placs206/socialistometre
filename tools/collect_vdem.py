#!/usr/bin/env python3
"""Collecte V-Dem (candidat d'audit C4 : propriété publique de l'économie, v2clstown ; diagnostic : capacité fiscale v2stfisccap).

Source : jeu V-Dem « Country-Year: V-Dem Full+Others », distribué par le paquet R officiel vdemdata (V-Dem Institute,
Université de Göteborg), fichier data/vdem.RData du dépôt github.com/vdeminstitute/vdemdata (version du paquet : DESCRIPTION).
Seules quelques colonnes (2015-2025) sont extraites dans data/raw/vdem_extrait.csv ; l'empreinte SHA-256 du fichier
complet téléchargé est consignée dans data/raw/MANIFEST.json. Mise à jour sur demande uniquement.
Usage : python3 tools/collect_vdem.py   (nécessite pyreadr)
"""
import datetime, hashlib, json, os, tempfile, urllib.request
import pyreadr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
URL = "https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/data/vdem.RData"
DESC = "https://raw.githubusercontent.com/vdeminstitute/vdemdata/master/DESCRIPTION"
COLS = ["country_name", "country_text_id", "year", "v2clstown", "v2clstown_osp", "v2clstown_codelow", "v2clstown_codehigh",
        "v2stfisccap", "v2stfisccap_osp"]


def main():
    tmp = os.path.join(tempfile.mkdtemp(), "vdem.RData")
    urllib.request.urlretrieve(URL, tmp)
    sha = hashlib.sha256(open(tmp, "rb").read()).hexdigest()
    version = [l.split(":", 1)[1].strip() for l in urllib.request.urlopen(DESC).read().decode().splitlines() if l.startswith("Version:")][0]
    df = list(pyreadr.read_r(tmp).values())[0]
    sub = df[[c for c in COLS if c in df.columns]]
    sub = sub[sub.year >= 2015].sort_values(["country_text_id", "year"])
    out = os.path.join(RAW, "vdem_extrait.csv")
    sub.to_csv(out, index=False, lineterminator="\n")
    man_p = os.path.join(RAW, "MANIFEST.json")
    man = json.load(open(man_p, encoding="utf-8"))
    man["fichiers"]["vdem_extrait.csv"] = {
        "url": URL, "date_collecte": datetime.date.today().isoformat(), "http": 200, "octets": os.path.getsize(out),
        "sha256": hashlib.sha256(open(out, "rb").read()).hexdigest(),
        "sha256_fichier_source_complet": sha, "version_source": f"vdemdata {version} (V-Dem Country-Year Full+Others)",
        "note": "Extrait (colonnes " + ", ".join(COLS) + " ; années ≥ 2015) du fichier vdem.RData ; candidat C4 et diagnostic de capacité fiscale (audit 2026-10-28)"}
    json.dump(man, open(man_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(out, len(sub), "lignes ; source", version, sha[:16])


if __name__ == "__main__":
    main()
