#!/usr/bin/env python3
"""Archive une édition : editions/v<version>/ (manifeste, paramètres, scores, tests, HTML) + empreintes SHA-256."""
import hashlib, json, os, shutil, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine")); import scoring as S
H = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()
dm = json.load(open(os.path.join(ROOT, "config/dimensions.json"), encoding="utf-8"))
sc = json.load(open(os.path.join(ROOT, "data/processed/scores.json"), encoding="utf-8"))
rob = json.load(open(os.path.join(ROOT, "docs/robustesse.json"), encoding="utf-8"))
v = dm["version_methodologie"]; d = os.path.join(ROOT, "editions", "v" + v); os.makedirs(d, exist_ok=True)
date = sys.argv[1] if len(sys.argv) > 1 else time.strftime("%Y-%m-%d")
files = ["data/raw/MANIFEST.json", "data/processed/pays.csv", "data/processed/observations.csv", "data/processed/indicateurs_alt.csv", "data/processed/anomalies.csv",
         "data/processed/scores.json", "data/processed/stabilite.json", "config/dimensions.json", "config/indicateurs.json", "corpus/principes.json",
         "corpus/verification_citations.json", "docs/robustesse.json", "dist/socialistometre.html"]
for f in ("data/processed/scores.json", "docs/robustesse.json", "dist/socialistometre.html"):
    shutil.copy(os.path.join(ROOT, f), os.path.join(d, os.path.basename(f)))
man = {"edition": "V" + v, "date_generation": date, "annee_donnees": sc["annee_cible"], "poids_dimensions": sc["poids_dimensions"],
       "empreinte_jeu_de_donnees_sha256": sc["empreinte_jeu_de_donnees"], "n_entites": sc["n_entites"], "n_avec_score_global": sc["n_avec_score_global"],
       "tests": {t["id"]: t["statut"] for t in rob["tests"]}, "echecs_critiques": rob["echecs_critiques"],
       "empreintes_fichiers": {f: H(f) for f in files},
       "reproduction": "python3 tools/build_dataset.py && python3 engine/scoring.py && python3 tools/run_robustness.py && python3 tools/build_html.py"}
json.dump(man, open(os.path.join(d, "MANIFEST.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print("édition archivée :", d)
