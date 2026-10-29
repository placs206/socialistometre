#!/usr/bin/env python3
"""Tests de cohérence de l'implémentation (brief d'audit, §24) — python3 -m unittest discover -s tests

Ces tests ne valident pas la pertinence doctrinale de la méthode : ils vérifient que l'implémentation fait exactement
ce que la configuration et le registre des décisions décrivent."""
import copy, csv, json, math, os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402

DIMS = "ABCD"


def synth(values, ind):
    """Jeu synthétique : values = {pays: {ind: valeur brute}}."""
    pays = {k: {"iso3": k, "nom_fr": k, "statut_politique": "État souverain", "type": "pays"} for k in values}
    obs = {k: {i: {"valeur_brute": float(v), "annee": 2023, "statut_validation": "valide"} for i, v in d.items()} for k, d in values.items()}
    return {"dim": {"dimensions": [{"id": "A", "poids": .45}, {"id": "B", "poids": .2}, {"id": "C", "poids": .2}, {"id": "D", "poids": .15}],
                    "version_methodologie": "test", "annee_cible": 2023},
            "ind": {"indicateurs": ind, "alternatives_sensibilite": []}, "pays": pays, "obs": obs, "alt": {}, "decisions": {"decisions": []}}


IND = [{"id": "A1", "dim": "A", "orientation": -1, "bornes": {"regle": "fixe", "bas": 0, "haut": 10}},
       {"id": "A2", "dim": "A", "orientation": 1, "bornes": {"regle": "fixe", "bas": 0, "haut": 4}},
       {"id": "B1", "dim": "B", "orientation": -1, "bornes": {"regle": "fixe", "bas": 0, "haut": 50}},
       {"id": "C1", "dim": "C", "orientation": 1, "bornes": {"regle": "fixe", "bas": 0, "haut": 1}},
       {"id": "D1", "dim": "D", "orientation": 1, "bornes": {"regle": "fixe", "bas": -4, "haut": 40}}]


class CasArtificiels(unittest.TestCase):
    def test_pole_liberal_100_et_socialisant_0(self):
        d = synth({"LIB": {"A1": 0, "A2": 4, "B1": 0, "C1": 1, "D1": 40}, "SOC": {"A1": 10, "A2": 0, "B1": 50, "C1": 0, "D1": -4}}, IND)
        res, _, _ = S.compute(d, overrides={})
        self.assertAlmostEqual(res["LIB"]["global"], 100.0)
        self.assertAlmostEqual(res["SOC"]["global"], 0.0)
        for k in DIMS:
            self.assertAlmostEqual(res["LIB"]["dims"][k], 100.0); self.assertAlmostEqual(res["SOC"]["dims"][k], 0.0)

    def test_indicateurs_inverses(self):
        d = synth({"X": {"A1": 2, "A2": 1}}, IND)
        n, _ = S.normalize(d, "minmax", "obs", S.indicator_defs(d))
        self.assertAlmostEqual(n["X"]["A1"], 80.0)   # −1 : 100·(10−2)/10
        self.assertAlmostEqual(n["X"]["A2"], 25.0)   # +1 : 100·1/4

    def test_valeur_extreme_sans_erreur_numerique(self):
        d = synth({"X": {"A1": 1e300, "A2": -1e300, "B1": float(1e12), "C1": 0.5, "D1": 0}}, IND)
        res, _, _ = S.compute(d, overrides={})
        for k in DIMS:
            v = res["X"]["dims"][k]
            self.assertTrue(v is not None and math.isfinite(v) and 0 <= v <= 100)

    def test_donnee_manquante_jamais_zero(self):
        d = synth({"X": {"A1": 5, "D1": 18}, "Y": {"A1": 5, "B1": 0, "D1": 18}}, IND)
        res, _, _ = S.compute(d, overrides={})
        self.assertIsNone(res["X"]["dims"]["B"])                       # absente, pas 0
        self.assertNotIn("B1", res["X"]["norm"])
        self.assertAlmostEqual(res["X"]["dims"]["A"], 50.0)            # moyenne sur les seuls indicateurs disponibles
        self.assertNotEqual(res["X"]["global"], res["Y"]["global"])     # Y a B = 100 : différence normale ; X n'est pas traité comme B = 0
        wx = (0.45 * 50 + 0.15 * 50) / 0.6
        self.assertAlmostEqual(res["X"]["global"], wx)

    def test_regle_minimum_indicateurs(self):
        d = synth({"X": {"A1": 0, "D1": 40}}, IND)
        r, _, _ = S.compute(d, overrides={"regles": {"min_indicateurs": {"A": 2}}})
        self.assertIsNone(r["X"]["dims"]["A"]); self.assertEqual(r["X"]["dimensions_insuffisantes"], ["A"]); self.assertIsNone(r["X"]["global"])
        r, _, _ = S.compute(d, overrides={})
        self.assertAlmostEqual(r["X"]["global"], 100.0)

    def test_regle_minimum_dimensions(self):
        d = synth({"X": {"A1": 0, "D1": 40}}, IND)
        r, _, _ = S.compute(d, overrides={"regles": {"min_dimensions": 3}})
        self.assertIsNone(r["X"]["global"])

    def test_modification_de_poids_et_contributions(self):
        d = synth({"X": {"A1": 0, "A2": 0, "B1": 25, "C1": 1, "D1": 18}}, IND)
        r, _, _ = S.compute(d, overrides={})
        self.assertAlmostEqual(sum(r["X"]["contributions"].values()), r["X"]["global"], places=9)
        # A = (100 + 0)/2 = 50 ; contribution A1 = 0,45 × 1/2 × 100
        self.assertAlmostEqual(r["X"]["contributions"]["A1"], 0.45 * 0.5 * 100)
        r2, _, _ = S.compute(d, overrides={"indicateurs": {"A1": {"poids_interne": 3}}})
        self.assertAlmostEqual(r2["X"]["dims"]["A"], 75.0)
        self.assertAlmostEqual(r2["X"]["contributions"]["A1"], 0.45 * 0.75 * 100)
        r3, _, _ = S.compute(d, overrides={"poids_dimensions": {"A": 0.25, "B": 0.25, "C": 0.25, "D": 0.25}})
        self.assertAlmostEqual(r3["X"]["global"], sum(r3["X"]["dims"][k] for k in DIMS) / 4)
        self.assertAlmostEqual(sum(r3["X"]["contributions"].values()), r3["X"]["global"], places=9)

    def test_exclusion_indicateur(self):
        d = synth({"X": {"A1": 0, "A2": 0, "D1": 40}}, IND)
        r, _, _ = S.compute(d, overrides={"indicateurs": {"A2": {"inclus": False}}})
        self.assertAlmostEqual(r["X"]["dims"]["A"], 100.0)
        self.assertNotIn("A2", r["X"]["contributions"])


class Reel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = S.load()
        cls.res, cls.params, cls.norm = S.compute(cls.data)
        cls.sc = json.load(open(os.path.join(ROOT, "data/processed/scores.json"), encoding="utf-8"))

    def test_poids_valides(self):
        w = S.dim_weights(self.data)
        self.assertAlmostEqual(sum(w.values()), 1.0)
        self.assertEqual(w, {"A": 0.45, "B": 0.2, "C": 0.2, "D": 0.15})
        for i in self.data["ind"]["indicateurs"]:
            self.assertGreater(float(i.get("poids_interne", 1)), 0)

    def test_valeurs_brutes_conservees(self):
        obs = {(r["iso3"], r["indicateur"]): float(r["valeur_brute"]) for r in csv.DictReader(open(os.path.join(ROOT, "data/processed/observations.csv"), encoding="utf-8"))}
        alt = {(r["iso3"], r["indicateur"]): float(r["valeur_brute"]) for r in csv.DictReader(open(os.path.join(ROOT, "data/processed/indicateurs_alt.csv"), encoding="utf-8"))}
        n = 0
        for iso, p in self.sc["pays"].items():
            for k, v in p["indicateurs"].items():
                self.assertEqual(v["brut"], obs.get((iso, k), alt.get((iso, k)))); n += 1
        self.assertGreaterEqual(n, len(obs))

    def test_sens_des_indicateurs(self):
        for k, pr in self.params.items():
            o = pr["orientation"]
            eff = S.apply_overrides(self.data, S.decisions_overrides(self.data))
            vals = sorted((eff["obs"][c][k]["valeur_brute"], self.norm[c][k]) for c in self.norm if k in self.norm[c])
            for (x1, s1), (x2, s2) in zip(vals, vals[1:]):
                if o > 0: self.assertLessEqual(s1, s2 + 1e-12, k)
                else: self.assertGreaterEqual(s1, s2 - 1e-12, k)

    def test_scores_dans_les_bornes(self):
        for r in self.res.values():
            for v in list(r["norm"].values()) + [x for x in r["dims"].values() if x is not None] + ([r["global"]] if r["global"] is not None else []):
                self.assertTrue(0 <= v <= 100)

    def test_contributions_totalisent_le_global(self):
        for k, r in self.res.items():
            if r["global"] is not None:
                self.assertAlmostEqual(sum(r["contributions"].values()), r["global"], places=9, msg=k)
            else:
                self.assertEqual(r["contributions"], {})

    def test_scores_partiels_signales(self):
        for k, p in self.sc["pays"].items():
            if p["statut_couverture"] in ("partiel", "insuffisant"):
                self.assertTrue(any("partiel" in a or "non calculé" in a for a in p["avertissements"]), k)
            if p["statut_couverture"] == "complet":
                self.assertEqual(p["dimensions_absentes"], [])

    def test_determinisme(self):
        a, _, _ = S.compute(self.data); b, _, _ = S.compute(S.load())
        self.assertEqual(json.dumps({k: (v["global"], v["dims"]) for k, v in a.items()}, sort_keys=True),
                         json.dumps({k: (v["global"], v["dims"]) for k, v in b.items()}, sort_keys=True))

    def test_methode_officielle_sans_decision_approuvee_egale_base(self):
        if any(d["statut"] == "approuvée" for d in self.data["decisions"]["decisions"]):
            self.skipTest("des décisions sont approuvées")
        b, _, _ = S.compute(self.data, overrides={})
        for k in b:
            self.assertEqual(b[k]["global"], self.res[k]["global"])

    def test_registre_coherent(self):
        ids = set()
        known = {i["id"] for i in self.data["ind"]["indicateurs"]} | {i["id"] for i in self.data["ind"]["alternatives_sensibilite"]}
        for d in self.data["decisions"]["decisions"]:
            self.assertNotIn(d["id"], ids); ids.add(d["id"])
            self.assertIn(d["categorie"], range(1, 9))
            self.assertIn(d["option_recommandee"], [o["id"] for o in d["options"]])
            self.assertIn(d["statut"], ("proposée", "approuvée", "rejetée"))
            if d["statut"] == "approuvée":
                self.assertIn(d["option_retenue"], [o["id"] for o in d["options"]])
            for o in d["options"]:
                p = o.get("patch") or {}
                for k in p.get("indicateurs", {}):
                    self.assertIn(k, known, (d["id"], o["id"], k))
                for k in p.get("ajouter", []):
                    self.assertIn(k, {i["id"] for i in self.data["ind"]["alternatives_sensibilite"]})
                S.compute(self.data, overrides=S.decisions_overrides(self.data, {d["id"]: o["id"]}))   # aucune option ne lève d'erreur

    def test_scenario_ne_modifie_pas_la_configuration(self):
        avant = json.dumps(self.data["ind"], sort_keys=True)
        S.compute(self.data, overrides=S.decisions_overrides(self.data, S.scenario_recommande(self.data)))
        self.assertEqual(avant, json.dumps(self.data["ind"], sort_keys=True))
        again, _, _ = S.compute(self.data)
        self.assertEqual({k: v["global"] for k, v in again.items()}, {k: v["global"] for k, v in self.res.items()})

    def test_identite_B5n(self):
        for iso, d in self.data["alt"].items():
            if "B5n" in d:
                o = self.data["obs"][iso]
                if o["B5"]["annee"] == d["B5n"]["annee"] == o["B6"]["annee"]:
                    self.assertAlmostEqual(d["B5n"]["valeur_brute"] + o["B6"]["valeur_brute"], o["B5"]["valeur_brute"], places=5)

    def test_bornes_figees_dec08_sans_effet(self):
        r, _, _ = S.compute(self.data, overrides=S.decisions_overrides(self.data, {"DEC-08": "figer"}))
        for k in r:
            if r[k]["global"] is not None:
                self.assertAlmostEqual(r[k]["global"], self.res[k]["global"], places=6)

    def test_recalcul_independant(self):
        p = subprocess.run([sys.executable, os.path.join(ROOT, "tools/audit/recalcul_independant.py")], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_scores_json_a_jour_avec_le_registre(self):
        out = S.build_output(self.data)
        self.assertEqual(out["empreinte_jeu_de_donnees"], self.sc["empreinte_jeu_de_donnees"])
        self.assertEqual({k: v["global"] for k, v in out["pays"].items()}, {k: v["global"] for k, v in self.sc["pays"].items()})


class Approbation(unittest.TestCase):
    """Le flux d'approbation dans une copie du dépôt : version incrémentée, méthode officielle modifiée, registre tracé."""
    def test_approbation_dans_une_copie(self):
        tmp = tempfile.mkdtemp()
        for sub in ("config", "data", "engine", "tools", "corpus", "docs"):
            shutil.copytree(os.path.join(ROOT, sub), os.path.join(tmp, sub), ignore=shutil.ignore_patterns("__pycache__"))
        v0 = json.load(open(os.path.join(ROOT, "config/dimensions.json"), encoding="utf-8"))["version_methodologie"]
        reg0 = json.load(open(os.path.join(ROOT, "config/decisions.json"), encoding="utf-8"))
        cur = [x for x in reg0["decisions"] if x["id"] == "DEC-06"][0]
        opt = "garder" if cur.get("option_retenue") == "echelle_naturelle" else "echelle_naturelle"
        r = subprocess.run([sys.executable, os.path.join(tmp, "tools/approve.py"), "DEC-06", opt, "--commentaire", "test"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        reg = json.load(open(os.path.join(tmp, "config/decisions.json"), encoding="utf-8"))
        d = [x for x in reg["decisions"] if x["id"] == "DEC-06"][0]
        self.assertEqual((d["statut"], d["option_retenue"]), ("approuvée", opt))
        self.assertTrue(d["empreinte_configuration"])
        v = json.load(open(os.path.join(tmp, "config/dimensions.json"), encoding="utf-8"))["version_methodologie"]
        self.assertNotEqual(v, v0)
        self.assertTrue(os.path.exists(os.path.join(tmp, "docs", f"COMPARAISON_V{v0}_V{v}.md")))
        code = ("import sys; sys.path.insert(0, %r); import scoring as S; d = S.load(); r,_,_ = S.compute(d); "
                "print(r['CHN']['norm']['D2'])") % os.path.join(tmp, "engine")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
        self.assertAlmostEqual(float(out), 100 * 2 / 44 if opt == "echelle_naturelle" else 0.0)   # D2 Chine = −2 : échelle −4–40 ou 0–40
        shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
