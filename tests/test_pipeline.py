"""Tests du pipeline V2 : import, correspondance, échelles, transformations, coordonnées, reproductibilité.

Exécution : python3 -m unittest tests.test_pipeline -v   (depuis la racine du dépôt)
Les tests marqués « critique » dans tools/validate.py bloquent la publication en cas d'échec.
"""
import copy
import csv
import json
import os
import random
import unittest

from src import coordinates as C
from src import transform as T
from src.common import PROC, RAW, REF, ROOT, config, read_csv, sha256_file

S = config("sources.json")["sources"]
P = config("parametres.json")
OBS = read_csv(os.path.join(PROC, "observations.csv"))
CORR = read_csv(os.path.join(REF, "correspondances.csv"))
PAYS = {p["iso3"]: p for p in read_csv(os.path.join(REF, "pays.csv"))}
COORD = json.load(open(os.path.join(PROC, "coordonnees.json"), encoding="utf-8"))
EXTR = {
    ("fraser", "efw2025"): read_csv(os.path.join(RAW, "fraser", "efw2025_extraction.csv")),
    ("heritage", "ief2026"): read_csv(os.path.join(RAW, "heritage", "ief2026_extraction.csv")),
    ("freedomhouse", "fiw2026"): read_csv(os.path.join(RAW, "freedomhouse", "fiw2026_extraction.csv")),
    ("freedomhouse", "fiw2013_2024"): read_csv(os.path.join(RAW, "freedomhouse", "fiw2013_2024_extraction.csv")),
    ("vdem", "v16"): read_csv(os.path.join(RAW, "vdem", "vdem_v16_extraction.csv")),
}
MAIN = {"fraser": "efw_summary", "heritage": "ief_overall", "vdem": "v2x_libdem", "freedomhouse": "fiw_total"}


class TestImport(unittest.TestCase):
    def test_effectifs_extractions(self):
        self.assertEqual(len(EXTR[("fraser", "efw2025")]), 165)  # EFW 2025 : 165 pays et territoires
        her = EXTR[("heritage", "ief2026")]
        self.assertEqual(len(her), 184)
        self.assertEqual(sum(1 for r in her if r["score"] != "N/A"), 176)
        self.assertEqual(len(EXTR[("freedomhouse", "fiw2026")]), 208)
        self.assertEqual(sum(1 for r in EXTR[("vdem", "v16")] if r["year"] == "2025"), 179)

    def test_fraser_coherence_interne(self):
        """Contrôle d'extraction : indice synthétique = moyenne des 5 domaines (méthode officielle) à l'arrondi près ;
        rang officiel = 1 + nombre de pays strictement mieux notés."""
        rows = EXTR[("fraser", "efw2025")]
        for r in rows:
            m = sum(float(r[f"area{k}"]) for k in range(1, 6)) / 5
            self.assertLessEqual(abs(m - float(r["summary"])), 0.011, r["nom_source"])
            exp = 1 + sum(1 for q in rows if float(q["summary"]) > float(r["summary"]))
            self.assertEqual(int(r["rang"]), exp, r["nom_source"])

    def test_heritage_rangs_et_bornes(self):
        rows = [r for r in EXTR[("heritage", "ief2026")] if r["score"] != "N/A"]
        self.assertEqual(sorted(int(r["rang_mondial"]) for r in rows), list(range(1, 177)))
        for r in rows:  # ordre des rangs compatible avec les scores publiés (égalités à l'arrondi tolérées)
            better = [q for q in rows if float(q["score"]) > float(r["score"])]
            self.assertGreaterEqual(int(r["rang_mondial"]), len(better) + 1, r["nom_source"])

    def test_freedomhouse_total_egal_pr_plus_cl(self):
        for k in (("freedomhouse", "fiw2026"), ("freedomhouse", "fiw2013_2024")):
            for r in EXTR[k]:
                self.assertEqual(int(r["total"]), int(r["pr"]) + int(r["cl"]), r)

    def test_extraction_reproductible_depuis_les_fichiers_officiels(self):
        """Si les fichiers sources sont présents (après tools/collect.py), la ré-extraction redonne exactement les CSV versionnés."""
        from src.importers import fraser, freedomhouse, heritage
        checks = [("fraser", "efw2025.pdf", lambda: fraser.extract_efw2025(), "fraser/efw2025_extraction.csv"),
                  ("heritage", "ief2026.pdf", lambda: heritage.extract(), "heritage/ief2026_extraction.csv"),
                  ("freedomhouse", "fiw2026_scores.html", lambda: freedomhouse.extract_2026(), "freedomhouse/fiw2026_extraction.csv")]
        done = 0
        for src, f, fn, out in checks:
            path = os.path.join(RAW, src, "_telechargements", f)
            if not os.path.exists(path):
                continue
            man = json.load(open(os.path.join(RAW, src, "MANIFEST.json"), encoding="utf-8"))["fichiers"][f]
            self.assertEqual(sha256_file(path), man["sha256"], f"{f} différent du fichier enregistré au manifeste")
            fresh = [{k: str(v) for k, v in r.items()} for r in fn()]
            self.assertEqual(fresh, read_csv(os.path.join(RAW, out)), out)
            done += 1
        if done == 0:
            self.skipTest("fichiers sources non téléchargés (tools/collect.py)")

    def test_manifestes_fichiers_versionnes(self):
        for src in ("fraser", "heritage", "vdem", "freedomhouse", "contexte"):
            man = json.load(open(os.path.join(RAW, src, "MANIFEST.json"), encoding="utf-8"))
            for f, m in man["fichiers"].items():
                for k in ("url", "date_collecte", "sha256"):
                    self.assertTrue(m.get(k), f"{src}/{f} : {k}")
                if m.get("versionne"):
                    self.assertEqual(sha256_file(os.path.join(RAW, src, f)), m["sha256"], f"{src}/{f}")


class TestGeo(unittest.TestCase):
    def test_toutes_les_entites_sources_sont_rattachees(self):
        keys = {(c["source"], c["edition"], c["code_source"] or c["nom_source"]) for c in CORR}
        for (src, ed), rows in EXTR.items():
            for r in rows:
                k = (src, ed, r["country_text_id"]) if src == "vdem" else (src, ed, r["nom_source"])
                self.assertIn(k, keys)

    def test_identifiants_valides_et_uniques(self):
        seen = set()
        for c in CORR:
            self.assertIn(c["iso3"], PAYS)
            self.assertIn(c["methode"], ("code_identique", "nom_identique", "manuel"))
            k = (c["source"], c["edition"], c["iso3"])
            self.assertNotIn(k, seen, f"deux entités sources rattachées au même identifiant : {k}")
            seen.add(k)
        self.assertEqual(len(PAYS), len({p for p in PAYS}))

    def test_cas_sensibles_documentes(self):
        m = {(c["source"], c["code_source"] or c["nom_source"]): c for c in CORR}
        self.assertEqual(m[("vdem", "PSE")]["iso3"], "X-WBK")  # V-Dem PSE = Cisjordanie seule
        self.assertTrue(m[("vdem", "PSE")]["note"])
        self.assertEqual(m[("freedomhouse", "Russian-occupied territories of Ukraine")]["iso3"], "X-RUA")


class TestDonnees(unittest.TestCase):
    def test_pas_de_doublon(self):
        k = [(o["iso3"], o["source"], o["edition"], o["indicateur"], o["annee_reference"]) for o in OBS]
        self.assertEqual(len(k), len(set(k)))

    def test_echelles_officielles(self):
        exp = {"fraser": (0, 10), "heritage": (0, 100), "vdem": (0, 1), "freedomhouse": (0, 100)}
        for src, (a, b) in exp.items():
            for ed, e in S[src]["editions"].items():
                if e["statut"] == "importee":
                    self.assertEqual((e["echelle"]["min"], e["echelle"]["max"]), (a, b), (src, ed))
        for o in OBS:
            if o["role"] == "principal":
                self.assertEqual((float(o["echelle_min"]), float(o["echelle_max"])), tuple(map(float, exp[o["source"]])))
            inside = T.in_scale(o["valeur_officielle"], o["echelle_min"], o["echelle_max"])
            self.assertEqual(inside, o["statut_validation"] != "hors_echelle_officielle", o)
            if not inside:
                self.assertEqual(o["source"], "freedomhouse", "seules les valeurs FH (question discrétionnaire) peuvent sortir de l'échelle")

    def test_transformation_exacte_et_reversible(self):
        for o in OBS:
            v, mn, mx, v100 = o["valeur_officielle"], o["echelle_min"], o["echelle_max"], float(o["valeur_0_100"])
            self.assertAlmostEqual(T.from_100(v100, mn, mx), float(v), places=6)
            self.assertAlmostEqual(v100, (float(v) - float(mn)) * 100 / (float(mx) - float(mn)), places=6)
        self.assertEqual(T.to_100("7.39", 0, 10), 73.9)
        self.assertEqual(T.to_100("0.8", 0, 1), 80.0)
        self.assertEqual(T.to_100("64.6", 0, 100), 64.6)

    def test_transformation_conserve_le_classement(self):
        groups = {}
        for o in OBS:
            groups.setdefault((o["source"], o["indicateur"], o["annee_reference"]), []).append(o)
        for k, g in groups.items():
            a = sorted(g, key=lambda o: (float(o["valeur_officielle"]), o["iso3"]))
            b = sorted(g, key=lambda o: (float(o["valeur_0_100"]), o["iso3"]))
            self.assertEqual([o["iso3"] for o in a], [o["iso3"] for o in b], k)

    def test_conservation_des_scores_sources(self):
        """La valeur officielle des observations est la chaîne exacte de l'extraction littérale."""
        idx = {(o["source"], o["edition"], o["nom_dans_source"], o["annee_reference"]): o["valeur_officielle"] for o in OBS if o["role"] == "principal"}
        for r in EXTR[("fraser", "efw2025")]:
            self.assertEqual(idx[("fraser", "efw2025", r["nom_source"], r["annee"])], r["summary"])
        for r in EXTR[("heritage", "ief2026")]:
            if r["score"] != "N/A":
                self.assertEqual(idx[("heritage", "ief2026", r["nom_source"], "2025")], r["score"])
        for r in EXTR[("freedomhouse", "fiw2026")]:
            self.assertEqual(idx[("freedomhouse", "fiw2026", r["nom_source"], r["annee"])], r["total"])
        for r in EXTR[("vdem", "v16")]:
            if r["v2x_libdem"]:
                self.assertEqual(idx[("vdem", "v16", r["country_name"], r["year"])], r["v2x_libdem"])

    def test_tracabilite_complete(self):
        for o in OBS:
            for k in ("url_source", "date_publication", "date_collecte", "sha256_source", "periode_debut", "periode_fin", "transformation"):
                self.assertTrue(o[k], (k, o["iso3"], o["source"]))

    def test_annees_et_periodes(self):
        for o in OBS:
            self.assertLessEqual(o["periode_debut"], o["periode_fin"])
            self.assertIn(o["annee_reference"], (o["periode_fin"][:4], o["periode_debut"][:4]))
            self.assertLessEqual(o["date_publication"][:4], "2026")
        her = [o for o in OBS if o["source"] == "heritage"]
        self.assertTrue(all(o["periode_debut"] == "2024-07-01" and o["periode_fin"] == "2025-06-30" for o in her))


class TestCoordonnees(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.R = C.compute()
        cls.series = C.load_principal()

    def test_fichier_a_jour_et_reproductible(self):
        self.assertEqual(json.loads(json.dumps(self.R)), COORD, "coordonnees.json n'est pas à jour : relancer src.coordinates")
        self.assertEqual(C.compute(), self.R)

    def test_un_seul_scenario_officiel_conforme_a_la_configuration(self):
        off = [k for k, s in self.R["scenarios"].items() if s["officiel"]]
        self.assertEqual(off, [self.R["scenario_officiel"]])
        s = self.R["scenarios"][off[0]]
        c = P["configuration_officielle"]
        self.assertEqual((s["x"], s["y"], s["mode"]), (c["axe_x"], c["axe_y"], c["mode_periode"]))
        self.assertEqual(off[0], "fraser|vdem|recent")

    def test_aucune_coordonnee_inventee(self):
        idx = {}
        for o in OBS:
            if o["role"] == "principal":
                idx[(o["iso3"], o["source"], o["edition"], int(o["annee_reference"]))] = float(o["valeur_0_100"])
        for sid, s in self.R["scenarios"].items():
            for iso, p in s["points"].items():
                for ax in ("x", "y"):
                    r = p[ax]
                    if r is None:
                        self.assertFalse(any(k[0] == iso and k[1] == s[ax]["source"] and (s["mode"] == "recent" or k[3] == int(s["mode"][6:]))
                                             for k in idx), (sid, iso, ax))
                    else:
                        self.assertEqual(idx[(iso, s[ax]["source"], r["ed"], r["an"])], r["v"], (sid, iso, ax))

    def test_donnee_manquante_jamais_zero(self):
        for s in self.R["scenarios"].values():
            for iso, p in s["points"].items():
                for ax in ("x", "y"):
                    if p[ax] is not None and p[ax]["v"] == 0:
                        self.assertEqual(float(p[ax]["off"]), 0.0)
                st = p["statut"]
                self.assertEqual(st == "complet", p["x"] is not None and p["y"] is not None)
        p = self.R["scenarios"]["fraser|vdem|recent"]["points"]
        self.assertIsNone(p["CUB"]["x"])  # Cuba : non couverte par EFW → absence, pas zéro
        self.assertIsNotNone(p["CUB"]["y"])

    def test_regles_de_periode(self):
        for sid, s in self.R["scenarios"].items():
            for iso, p in s["points"].items():
                for ax in ("x", "y"):
                    r = p[ax]
                    if r is None:
                        continue
                    lst = self.series[(s[ax]["source"], s[ax]["indicateur"])][iso]
                    if s["mode"] == "recent":
                        self.assertEqual(r["an"], max(o["annee_reference"] for o in lst))
                    else:
                        self.assertEqual(r["an"], int(s["mode"].split(":")[1]))
                if p["ecart"] is not None:
                    self.assertGreaterEqual(p["ecart"], 0)
        fra = self.R["scenarios"]["fraser|vdem|annee:2023"]["points"]["FRA"]
        self.assertEqual(fra["ecart"], 0.0)
        self.assertEqual(self.R["scenarios"]["fraser|vdem|recent"]["points"]["FRA"]["ecart"], 2.0)

    def test_independance_ordre_des_lignes(self):
        orig = C.read_csv

        def shuffled(path):
            rows = orig(path)
            random.Random(7).shuffle(rows)
            return rows
        C.read_csv = shuffled
        try:
            r2 = C.compute()
        finally:
            C.read_csv = orig
        self.assertEqual(r2["scenarios"], self.R["scenarios"])
        self.assertEqual(r2["divergences"], self.R["divergences"])

    def test_changer_de_source_ne_modifie_pas_les_donnees_brutes(self):
        files = [os.path.join(RAW, k[0], f"{k[1]}_extraction.csv") for k in EXTR if k[0] != "vdem"] + [os.path.join(PROC, "observations.csv")]
        before = {f: sha256_file(f) for f in files}
        for sid in self.R["scenarios"]:
            C.scenario(self.series, PAYS, self.R["scenarios"][sid]["x"], self.R["scenarios"][sid]["y"], self.R["scenarios"][sid]["mode"])
        self.assertEqual(before, {f: sha256_file(f) for f in files})

    def test_pas_de_moyenne_entre_sources(self):
        for s in self.R["scenarios"].values():
            for iso, p in s["points"].items():
                if p["x"]:
                    self.assertIn(p["x"]["ed"], S[s["x"]["source"]]["editions"])
                if p["y"]:
                    self.assertIn(p["y"]["ed"], S[s["y"]["source"]]["editions"])

    def test_contexte_sans_effet_sur_les_coordonnees(self):
        path = os.path.join(PROC, "contexte.csv")
        saved = open(path, "rb").read()
        try:
            rows = list(csv.DictReader(open(path, encoding="utf-8")))
            for r in rows:
                r["valeur"] = "999999"
            with open(path, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
                w.writeheader(); w.writerows(rows)
            r2 = C.compute()
        finally:
            open(path, "wb").write(saved)
        self.assertEqual(r2["scenarios"], self.R["scenarios"])

    def test_divergences_descriptives(self):
        for iso, d in self.R["divergences"].items():
            for axe, v in d.items():
                self.assertEqual(v["forte"], abs(v["diff"]) >= P["seuil_divergence_points"])


if __name__ == "__main__":
    unittest.main()
