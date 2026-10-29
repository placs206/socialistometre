#!/usr/bin/env python3
"""Chaîne complète de validation d'une édition : construction, calcul, HTML, tests, rapport.

1. python3 -m src.build ; python3 -m src.coordinates ; tools/compare_v1.py
2. tests du pipeline et de l'interface (unittest) ; résultats test par test dans docs/validation.json
3. reconstruction de index.html (avec le rapport intégré) puis nouvelle exécution des tests d'interface sur le fichier final
Code de sortie 1 si un test critique échoue (publication bloquée).
Usage : python3 tools/validate.py [AAAA-MM-JJ]
"""
import io
import json
import os
import subprocess
import sys
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
NON_CRITIQUES = {"test_07_onglets_recherche_tri_comparaison", "test_08_zoom_et_reinitialisation",
                 "test_10_contestation_sans_effet_sur_les_donnees", "test_11_mobile_sans_debordement"}


def sh(*cmd):
    subprocess.run(cmd, cwd=ROOT, check=True)


def run_suite(mod):
    suite = unittest.defaultTestLoader.loadTestsFromName(mod)
    ids = []

    def collect(s):
        for t in s:
            if isinstance(t, unittest.TestSuite):
                collect(t)
            else:
                ids.append(t.id())
    collect(suite)
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    bad = {t.id(): "ÉCHEC" for t, _ in res.failures} | {t.id(): "ERREUR" for t, _ in res.errors}
    skip = {t.id(): "IGNORÉ (" + r + ")" for t, r in res.skipped}
    out = []
    for tid in ids:
        name = tid.split(".")[-1]
        out.append({"module": mod, "nom": name, "resultat": bad.get(tid, skip.get(tid, "RÉUSSI")),
                    "critique": name not in NON_CRITIQUES,
                    "detail": next((tb.strip().splitlines()[-1] for tt, tb in res.failures + res.errors if tt.id() == tid), "")})
    return out


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else time.strftime("%Y-%m-%d")
    os.environ["PYTHONWARNINGS"] = "ignore"
    sh(sys.executable, "-m", "src.build")
    sh(sys.executable, "-m", "src.coordinates")
    sh(sys.executable, "tools/compare_v1.py")
    sh(sys.executable, "tools/build_html.py")
    tests = run_suite("tests.test_pipeline") + run_suite("tests.test_html")
    crit = [t for t in tests if t["critique"] and t["resultat"] in ("ÉCHEC", "ERREUR")]
    rep = {"date": date, "statut": "VALIDÉ" if not crit else "BLOQUÉ (test critique échoué)",
           "n_tests": len(tests), "n_reussis": sum(t["resultat"] == "RÉUSSI" for t in tests),
           "n_ignores": sum(t["resultat"].startswith("IGNORÉ") for t in tests), "echecs_critiques": [t["nom"] for t in crit],
           "tests": tests}
    json.dump(rep, open(os.path.join(ROOT, "docs", "validation.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    sh(sys.executable, "tools/build_html.py")
    final = run_suite("tests.test_html")
    fcrit = [t for t in final if t["critique"] and t["resultat"] in ("ÉCHEC", "ERREUR")]
    print(f"{rep['statut']} : {rep['n_reussis']}/{rep['n_tests']} réussis, {rep['n_ignores']} ignoré(s) ; "
          f"HTML final : {sum(t['resultat'] == 'RÉUSSI' for t in final)}/{len(final)}")
    for t in tests + final:
        if t["resultat"] != "RÉUSSI":
            print(" ", t["module"], t["nom"], t["resultat"], t["detail"])
    return 1 if crit or fcrit else 0


if __name__ == "__main__":
    sys.exit(main())
