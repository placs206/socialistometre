#!/usr/bin/env python3
"""Archive une édition V2 dans editions/v<version>/ : manifeste (paramètres, éditions des sources, empreintes SHA-256,
résultats des tests), coordonnées calculées, rapport de validation et HTML publié.
Les données complètes (extractions, observations) restent versionnées dans git ; le manifeste fixe leurs empreintes.
Refuse d'archiver si la validation n'est pas « VALIDÉ ».
Usage : python3 tools/make_edition.py AAAA-MM-JJ
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.common import ROOT, config, read_json, sha256_file, write_json  # noqa: E402

FILES = ["config/sources.json", "config/parametres.json", "config/contexte.json", "data/reference/pays.csv",
         "data/reference/correspondances.csv", "data/raw/fraser/efw2025_extraction.csv", "data/raw/heritage/ief2026_extraction.csv",
         "data/raw/vdem/vdem_v16_extraction.csv", "data/raw/freedomhouse/fiw2026_extraction.csv",
         "data/raw/freedomhouse/fiw2013_2024_extraction.csv", "data/processed/observations.csv", "data/processed/contexte.csv",
         "data/processed/anomalies.csv", "data/processed/coordonnees.json", "docs/validation.json", "index.html"]


def main():
    date = sys.argv[1]
    par = config("parametres.json")
    val = read_json(os.path.join(ROOT, "docs", "validation.json"))
    if val["statut"] != "VALIDÉ":
        sys.exit("validation non réussie : édition non archivée")
    co = read_json(os.path.join(ROOT, "data", "processed", "coordonnees.json"))
    S = config("sources.json")["sources"]
    d = os.path.join(ROOT, "editions", "v" + par["version_methodologie"])
    os.makedirs(d, exist_ok=True)
    for f in ("data/processed/coordonnees.json", "docs/validation.json", "index.html"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(d, os.path.basename(f)))
    man = {"edition": "V" + par["version_methodologie"], "date_generation": date, "parametres": par,
           "editions_sources": {k: {e: v.get("statut") for e, v in s["editions"].items()} for k, s in S.items()},
           "empreinte_jeu_de_donnees_sha256": co["empreinte_jeu_de_donnees"],
           "comptes_scenario_officiel": co["scenarios"][co["scenario_officiel"]]["comptes"],
           "tests": {"statut": val["statut"], "reussis": val["n_reussis"], "total": val["n_tests"], "ignores": val["n_ignores"]},
           "empreintes_fichiers": {f: sha256_file(os.path.join(ROOT, f)) for f in FILES},
           "reproduction": "python3 tools/validate.py AAAA-MM-JJ (après éventuellement python3 tools/collect.py et ré-extraction)"}
    write_json(os.path.join(d, "MANIFEST.json"), man)
    print("édition archivée :", d)


if __name__ == "__main__":
    main()
