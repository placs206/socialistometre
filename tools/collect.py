#!/usr/bin/env python3
"""Collecte des fichiers sources officiels (mise à jour à la demande uniquement).

Télécharge les fichiers TELS QUELS dans data/raw/<source>/_telechargements/ (dossier non versionné quand la
redistribution n'est pas autorisée) et met à jour data/raw/<source>/MANIFEST.json : URL, date de collecte,
statut HTTP, taille, SHA-256, licence, versionné ou non.

Aucune transformation, aucune valeur fabriquée. Une source inaccessible est signalée, jamais remplacée.

Usage : python3 tools/collect.py [fraser|heritage|freedomhouse|vdem|contexte ...] [--date AAAA-MM-JJ]
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.common import DL, RAW, manifest, save_manifest, sha256_file  # noqa: E402

UA = {"User-Agent": "socialistometre-collector/2.0 (recherche; depot GitHub placs206/socialistometre)"}

FILES = {
    "fraser": [("efw2025.pdf", "https://www.libinst.ch/wp-content/uploads/2025/09/EFOTW-2025.pdf",
                "Rapport officiel EFW 2025 (copie du membre de l'Economic Freedom Network Liberales Institut)", False)],
    "heritage": [("ief2026.pdf", "https://static.heritage.org/index/pdf/2026/2026_indexofeconomicfreedom.pdf",
                  "Rapport officiel 2026 Index of Economic Freedom (PDF, 428 p.)", False)],
    "freedomhouse": [("fiw2026_scores.html", "https://freedomhouse.org/countries/freedom-world/scores",
                      "Page officielle « Global Freedom Scores » (édition FIW 2026)", False)],
}
VDEM_REPO = "https://github.com/vdeminstitute/vdemdata"
VDEM_COMMIT = "f4dd26922e658442524dfd954bf14f7ebe622d5d"
WB = [  # indicateurs contextuels Banque mondiale (WDI, source 2)
    ("GC.XPN.TOTL.GD.ZS", "Charges des administrations publiques (% du PIB)"),
    ("GC.TAX.TOTL.GD.ZS", "Recettes fiscales (% du PIB)"),
    ("NE.CON.GOVT.ZS", "Consommation finale des administrations publiques (% du PIB)"),
    ("GC.REV.SOCL.ZS", "Cotisations sociales (% des recettes)"),
    ("NY.GDP.PCAP.PP.KD", "PIB par habitant, PPA ($ internationaux constants 2021)"),
]


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"échec {url} : {last}")


def record(man, name, url, path, status, ctype, note, versionne):
    man["fichiers"][name] = {"url": url, "date_collecte": DATE, "http": status, "content_type": ctype,
                             "octets": os.path.getsize(path), "sha256": sha256_file(path), "note": note,
                             "versionne": versionne}
    print(f"OK {name} {os.path.getsize(path)} o")


def simple(src):
    man = manifest(src)
    for name, url, note, versionne in FILES[src]:
        d = os.path.join(RAW, src, "" if versionne else DL)
        os.makedirs(d, exist_ok=True)
        st, ct, data = fetch(url)
        if ("pdf" in name and not data.startswith(b"%PDF")) or (name.endswith(".html") and b"<html" not in data[:2000].lower()):
            raise RuntimeError(f"{url} : contenu inattendu ({ct}) — page anti-robots probable ; fichier NON enregistré")
        path = os.path.join(d, name)
        open(path, "wb").write(data)
        record(man, name, url, path, st, ct, note, versionne)
    save_manifest(src, man)


def vdem():
    man = manifest("vdem")
    d = os.path.join(RAW, "vdem", DL, "vdemdata")
    if not os.path.isdir(os.path.join(d, ".git")):
        subprocess.run(["git", "clone", "--depth", "50", VDEM_REPO, d], check=True, env={**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"})
    subprocess.run(["git", "-C", d, "checkout", "-q", VDEM_COMMIT], check=True)
    for f in ("data/vdem.RData", "data/codebook.RData", "DESCRIPTION"):
        record(man, f.split("/")[-1], f"{VDEM_REPO}/blob/{VDEM_COMMIT}/{f}", os.path.join(d, f), 200, "", "Paquet officiel vdemdata 16.0", False)
    save_manifest("vdem", man)


def contexte():
    man = manifest("contexte")
    for code, label in WB:
        url = f"https://api.worldbank.org/v2/country/all/indicator/{code}?date=2015:2025&format=json&per_page=20000&source=2"
        st, ct, data = fetch(url)
        js = json.loads(data)
        if not isinstance(js, list) or len(js) < 2 or js[0].get("pages", 1) != 1:
            raise RuntimeError(f"{code} : réponse API inattendue")
        path = os.path.join(RAW, "contexte", f"wb_{code}.json")
        open(path, "wb").write(data)
        record(man, f"wb_{code}.json", url, path, st, ct, f"WDI : {label}", True)
    st, ct, data = fetch("https://api.worldbank.org/v2/country?format=json&per_page=400")
    path = os.path.join(RAW, "contexte", "wb_countries.json")
    open(path, "wb").write(data)
    record(man, "wb_countries.json", "https://api.worldbank.org/v2/country?format=json&per_page=400", path, st, ct,
           "Métadonnées pays Banque mondiale (région, revenu)", True)
    save_manifest("contexte", man)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    DATE = sys.argv[sys.argv.index("--date") + 1] if "--date" in sys.argv else time.strftime("%Y-%m-%d")
    args = [a for a in args if a != DATE] or ["fraser", "heritage", "freedomhouse", "vdem", "contexte"]
    for s in args:
        try:
            {"vdem": vdem, "contexte": contexte}.get(s, lambda s=s: simple(s))()
        except Exception as e:  # noqa: BLE001
            print(f"ÉCHEC {s} : {e}", file=sys.stderr)
