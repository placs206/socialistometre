"""Tests automatisés du moteur (python3 -m unittest discover -s tests)."""
import json, math, os, random, sys, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402


def tiny():
    """Jeu synthétique minimal pour tester les règles de calcul."""
    ind = {"A1": {"dim": "A", "orientation": -1, "bornes": {"regle": "fixe", "bas": 0, "haut": 10}},
           "B1": {"dim": "B", "orientation": 1, "bornes": {"regle": "fixe", "bas": 0, "haut": 100}},
           "C1": {"dim": "C", "orientation": 1, "bornes": {"regle": "fixe", "bas": 0, "haut": 1}},
           "D1": {"dim": "D", "orientation": 1, "bornes": {"regle": "fixe", "bas": -2, "haut": 2}}}
    return ind


class TestNormalisation(unittest.TestCase):
    def test_orientation_et_bornes(self):
        data = {"obs": {"X": {"A1": {"valeur_brute": 0.0}}, "Y": {"A1": {"valeur_brute": 10.0}}, "Z": {"A1": {"valeur_brute": 15.0}}}}
        norm, _ = S.normalize(data, "minmax", "obs", tiny())
        self.assertAlmostEqual(norm["X"]["A1"], 100.0)   # droit de douane nul → pôle libéral
        self.assertAlmostEqual(norm["Y"]["A1"], 0.0)
        self.assertAlmostEqual(norm["Z"]["A1"], 0.0)     # écrêtage à la borne

    def test_percentile_numpy(self):
        v = sorted([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5])
        try:
            import numpy as np
        except ImportError:
            self.skipTest("numpy absent")
        for p in (5, 50, 95):
            self.assertAlmostEqual(S.percentile(v, p), float(np.percentile(v, p)))

    def test_bornes_monotones(self):
        data = {"obs": {str(i): {"A1": {"valeur_brute": float(i)}} for i in range(11)}}
        norm, _ = S.normalize(data, "minmax", "obs", tiny())
        vals = [norm[str(i)]["A1"] for i in range(11)]
        self.assertEqual(vals, sorted(vals, reverse=True))


class TestScores(unittest.TestCase):
    W = {"A": 0.45, "B": 0.20, "C": 0.20, "D": 0.15}
    DIM = {"A1": "A", "B1": "B", "C1": "C", "D1": "D"}

    def test_complet(self):
        r = S.score_country({"A1": 80, "B1": 40, "C1": 60, "D1": 100}, self.DIM, self.W)
        self.assertAlmostEqual(r["global"], 0.45 * 80 + 0.2 * 40 + 0.2 * 60 + 0.15 * 100)

    def test_renormalisation(self):
        r = S.score_country({"A1": 80, "D1": 100}, self.DIM, self.W)
        self.assertAlmostEqual(r["global"], (0.45 * 80 + 0.15 * 100) / 0.60)

    def test_sans_dimension_a_pas_de_global(self):
        r = S.score_country({"B1": 100, "C1": 100}, self.DIM, self.W)
        self.assertIsNone(r["global"])
        self.assertAlmostEqual(r["dims"]["B"], 100)

    def test_une_seule_dimension(self):
        self.assertIsNone(S.score_country({"A1": 90}, self.DIM, self.W)["global"])

    def test_moyenne_dans_dimension(self):
        dim = {"A1": "A", "A2": "A"}
        r = S.score_country({"A1": 10, "A2": 30, "D1": 50}, {**dim, "D1": "D"}, self.W)
        self.assertAlmostEqual(r["dims"]["A"], 20)

    def test_rangs_ex_aequo(self):
        r = S.competition_rank({"a": 90.0, "b": 80.0, "c": 80.0, "d": 10.0, "e": None})
        self.assertEqual([r["a"], r["b"], r["c"], r["d"]], [1, 2, 2, 4])
        self.assertNotIn("e", r)

    def test_spearman(self):
        self.assertAlmostEqual(S.spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(S.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)


class TestDonnees(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = S.load()
        cls.res, cls.params, cls.norm = S.compute(cls.data)

    def test_poids_somment_a_un(self):
        self.assertAlmostEqual(sum(S.dim_weights(self.data).values()), 1.0)
        self.assertEqual(S.dim_weights(self.data), {"A": 0.45, "B": 0.20, "C": 0.20, "D": 0.15})

    def test_scores_dans_0_100(self):
        for iso3, r in self.res.items():
            for v in list(r["dims"].values()) + [r["global"]] + list(r["norm"].values()):
                if v is not None:
                    self.assertTrue(-1e-9 <= v <= 100 + 1e-9, (iso3, v))

    def test_pas_de_doublon(self):
        import csv
        rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "processed", "observations.csv"), encoding="utf-8")))
        keys = [(r["iso3"], r["indicateur"]) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))

    def test_tracabilite_complete(self):
        for iso3, d in self.data["obs"].items():
            for k, o in d.items():
                for champ in ("source", "url_source", "date_collecte", "transformation", "statut_validation", "annee", "unite"):
                    self.assertTrue(o[champ] not in ("", None), (iso3, k, champ))
                self.assertIn(iso3, self.data["pays"])

    def test_global_exige_dimension_a(self):
        for iso3, r in self.res.items():
            if r["global"] is not None:
                self.assertIsNotNone(r["dims"]["A"], iso3)

    def test_orientation_tarifs(self):
        # Un pays à droits nuls doit être plus libéral qu'un pays à droits élevés sur A1
        o = {i: r["A1"]["valeur_brute"] for i, r in self.data["obs"].items() if "A1" in r}
        lo = min(o, key=o.get); hi = max(o, key=o.get)
        self.assertGreater(self.norm[lo]["A1"], self.norm[hi]["A1"])

    def test_sortie_deterministe(self):
        a = json.dumps(S.build_output(self.data), sort_keys=True)
        b = json.dumps(S.build_output(S.load()), sort_keys=True)
        self.assertEqual(a, b)

    def test_scores_json_a_jour(self):
        on_disk = json.load(open(os.path.join(ROOT, "data", "processed", "scores.json"), encoding="utf-8"))
        fresh = json.loads(json.dumps(S.build_output(self.data), sort_keys=True))
        self.assertEqual(on_disk, fresh)


if __name__ == "__main__":
    unittest.main()
