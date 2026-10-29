"""Tests de l'explorateur autonome index.html (Chromium/Playwright, navigateur hors ligne).

Exécution : python3 -m unittest tests.test_html -v
"""
import json
import os
import re
import unittest

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
CO = json.load(open(os.path.join(ROOT, "data", "processed", "coordonnees.json"), encoding="utf-8"))


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.br = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.br.close()
        cls.pw.stop()

    def page(self, w=1280, h=900):
        ctx = self.br.new_context(viewport={"width": w, "height": h}, offline=True)
        p = ctx.new_page()
        self.errs, self.reqs = [], []
        p.on("pageerror", lambda e: self.errs.append(str(e)))
        p.on("console", lambda m: m.type == "error" and self.errs.append(m.text))
        p.on("request", lambda r: not r.url.startswith(("file:", "data:", "about:", "blob:")) and self.reqs.append(r.url))
        p.goto("file://" + HTML)
        p.wait_for_selector("#chart circle")
        return p

    def test_01_aucune_ressource_externe(self):
        s = open(HTML, encoding="utf-8").read()
        self.assertEqual(re.findall(r'<(?:script|link|img|iframe)[^>]+(?:src|href)=["\']https?://', s), [])
        self.assertNotIn("@import", s)
        self.assertNotIn("url(http", s)

    def test_02_hors_ligne_sans_erreur(self):
        p = self.page()
        self.assertEqual(self.errs, [])
        self.assertEqual(self.reqs, [])
        n = CO["scenarios"][CO["scenario_officiel"]]["comptes"]["complet"]
        self.assertEqual(p.locator("#chart circle").count(), n)

    def test_03_parite_graphique_donnees(self):
        p = self.page()
        res = p.evaluate("()=>{var s=__socialistometre.scen();return Object.keys(s.p).map(function(i){var r=s.p[i];return [i,r[0]?r[0][0]:null,r[1]?r[1][0]:null,r[3]];});}")
        off = CO["scenarios"][CO["scenario_officiel"]]["points"]
        self.assertEqual(len(res), len(off))
        for i, x, y, st in res:
            o = off[i]
            self.assertEqual(x, o["x"]["v"] if o["x"] else None, i)
            self.assertEqual(y, o["y"]["v"] if o["y"] else None, i)
        # position des cercles = coordonnées
        c = p.evaluate("()=>{var c=document.querySelector('#chart circle[data-id=FRA]');return [+c.getAttribute('cx'),+c.getAttribute('cy')];}")
        fra = off["FRA"]
        exp = p.evaluate("(v)=>{var W=+document.getElementById('chart').getAttribute('viewBox').split(' ')[2],H=+document.getElementById('chart').getAttribute('viewBox').split(' ')[3];var M={l:58,r:16,t:16,b:52};return [M.l+(v[0]+2)/104*(W-M.l-M.r),H-M.b-(v[1]+2)/104*(H-M.t-M.b)];}", [fra["x"]["v"], fra["y"]["v"]])
        self.assertAlmostEqual(c[0], exp[0], places=1)
        self.assertAlmostEqual(c[1], exp[1], places=1)

    def test_04_fiche_coherente_avec_le_graphique(self):
        p = self.page()
        p.evaluate("()=>__socialistometre.openFiche('FRA')")
        txt = p.inner_text("#fiche")
        o = CO["scenarios"][CO["scenario_officiel"]]["points"]["FRA"]
        fmt = lambda v: f"{v:.1f}".replace(".", ",")
        self.assertIn(fmt(o["x"]["v"]) + " ; " + fmt(o["y"]["v"]), txt)
        for s in ("Fraser", "V-Dem", "Heritage", "Freedom House", "Composantes officielles", "Données contextuelles", "Contester un score"):
            self.assertIn(s, txt)
        self.assertEqual(self.errs, [])

    def test_05_mode_comparaison_distinct_et_donnees_intactes(self):
        p = self.page()
        before = p.evaluate("()=>JSON.stringify(__socialistometre.D.obs)+JSON.stringify(__socialistometre.D.scen)")
        self.assertIn("Configuration officielle", p.inner_text("#modebar"))
        p.select_option("#xs", "heritage")
        self.assertIn("Mode comparaison", p.inner_text("#modebar"))
        self.assertIn("cmp", p.get_attribute("#modebar", "class"))
        n = CO["scenarios"]["heritage|vdem|recent"]["comptes"]["complet"]
        self.assertEqual(p.locator("#chart circle").count(), n)
        p.select_option("#ys", "freedomhouse")
        p.click("#reset")
        self.assertIn("Configuration officielle", p.inner_text("#modebar"))
        after = p.evaluate("()=>JSON.stringify(__socialistometre.D.obs)+JSON.stringify(__socialistometre.D.scen)")
        self.assertEqual(before, after)
        self.assertEqual(self.errs, [])

    def test_06_absence_affichee_jamais_zero(self):
        p = self.page()
        p.click("nav button[data-t=tableau]")
        p.fill("#tq", "Cuba")
        row = p.inner_text("#tbl tbody tr")
        self.assertIn("—", row)
        self.assertIn("Politique seulement", row)
        p.click("nav button[data-t=incomplets]")
        self.assertIn("Cuba", p.inner_text("#inc"))

    def test_07_onglets_recherche_tri_comparaison(self):
        p = self.page()
        for t in ("tableau", "fiche", "comparer", "incomplets", "methode", "correspondances", "graphique"):
            p.click(f"nav button[data-t={t}]")
            self.assertTrue(p.is_visible(f"#s-{t}"), t)
        p.fill("#q", "France")
        self.assertGreaterEqual(p.locator("#chart text", has_text="France").count(), 1)
        p.click("nav button[data-t=tableau]")
        p.click("#tbl th[data-k=x]")
        p.click("nav button[data-t=comparer]")
        p.select_option("#csel", "DNK"); p.click("#cadd")
        p.select_option("#csel", "SGP"); p.click("#cadd")
        self.assertEqual(p.locator("#cmp thead th").count(), 3)
        p.click("nav button[data-t=methode]")
        self.assertIn("non importée", p.inner_text("#meth"))
        self.assertEqual(self.errs, [])

    def test_08_zoom_et_reinitialisation(self):
        p = self.page()
        p.click("#zin"); p.click("#zin")
        self.assertIsNotNone(p.evaluate("()=>__socialistometre.S.view"))
        p.click("#zreset")
        self.assertIsNone(p.evaluate("()=>__socialistometre.S.view"))

    def test_09_periode_commune(self):
        p = self.page()
        p.select_option("#mode", "annee:2023")
        self.assertIn("Mode comparaison", p.inner_text("#modebar"))
        self.assertEqual(p.locator("#chart circle").count(), CO["scenarios"]["fraser|vdem|annee:2023"]["comptes"]["complet"])
        self.assertIn("(0 point(s))", p.inner_text("#legend"))

    def test_10_contestation_sans_effet_sur_les_donnees(self):
        p = self.page()
        before = p.evaluate("()=>JSON.stringify(__socialistometre.D.obs)")
        p.evaluate("()=>__socialistometre.openFiche('USA')")
        p.fill("#ct-motif", "Test de contestation")
        p.click("#ct-save")
        self.assertIn("Test de contestation", p.inner_text("#fiche"))
        self.assertEqual(before, p.evaluate("()=>JSON.stringify(__socialistometre.D.obs)"))

    def test_12_noms_g20_et_clic_affiche_le_nom(self):
        p = self.page()
        n = p.locator("#chart text.lbl").count()
        self.assertGreaterEqual(n, 15)
        self.assertLessEqual(n, 19)  # seulement une sélection, pas les 162 pays
        self.assertEqual(p.locator("#chart text.lbl[data-for=CHL]").count(), 0)
        bb = p.locator("#chart circle[data-id=CHL]").bounding_box()
        p.mouse.click(bb["x"] + bb["width"] / 2 + 3, bb["y"] + bb["height"] / 2)  # clic légèrement à côté : point le plus proche
        self.assertIn("Chili", p.inner_text("#pick"))
        self.assertEqual(p.locator("#chart text.lbl[data-for=CHL]").count(), 1)  # le nom reste affiché
        p.click("#pick button[data-a=fiche]")
        self.assertTrue(p.is_visible("#s-fiche"))
        self.assertIn("Chili", p.inner_text("#fiche"))
        self.assertEqual(self.errs, [])

    def test_11_mobile_sans_debordement(self):
        p = self.page(390, 844)
        self.assertLessEqual(p.evaluate("()=>document.documentElement.scrollWidth"), 390)
        p.evaluate("()=>__socialistometre.openFiche('FRA')")
        self.assertLessEqual(p.evaluate("()=>document.documentElement.scrollWidth"), 390)
        self.assertEqual(self.errs, [])


if __name__ == "__main__":
    unittest.main()
