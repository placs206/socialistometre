#!/usr/bin/env python3
"""Tests de l'explorateur HTML autonome (Chromium/Playwright) : hors-ligne, erreurs JS, parité JS/Python, fonctionnalités, mobile."""
import json, os, re, sys, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "dist", "socialistometre.html")
SC = json.load(open(os.path.join(ROOT, "data/processed/scores.json"), encoding="utf-8"))["pays"]
from playwright.sync_api import sync_playwright

class T(unittest.TestCase):
    @classmethod
    def setUpClass(c):
        c.pw = sync_playwright().start(); c.br = c.pw.chromium.launch()
    @classmethod
    def tearDownClass(c):
        c.br.close(); c.pw.stop()
    def page(self, w=1280, h=900):
        ctx = self.br.new_context(viewport={"width": w, "height": h}, offline=True)
        p = ctx.new_page(); self.errs = []; self.reqs = []
        p.on("pageerror", lambda e: self.errs.append(str(e)))
        p.on("console", lambda m: m.type == "error" and self.errs.append(m.text))
        p.on("request", lambda r: not r.url.startswith(("file:", "data:", "about:")) and self.reqs.append(r.url))
        p.goto("file://" + HTML); return p
    def test_01_statique_aucune_ressource_externe(self):
        s = open(HTML, encoding="utf-8").read()
        self.assertEqual(re.findall(r'<(?:script|link|img|iframe)[^>]+(?:src|href)=["\']https?://', s), [])
        self.assertNotIn("@import", s); self.assertNotIn("url(http", s)
    def test_02_chargement_hors_ligne_sans_erreur(self):
        p = self.page(); p.wait_for_selector("#swarm circle")
        self.assertEqual(self.errs, []); self.assertEqual(self.reqs, [])
        self.assertGreater(p.locator("#swarm circle").count(), 200)
    def test_03_parite_js_python(self):
        p = self.page()
        res = p.evaluate("()=>__socialistometre.P.map(function(x){return [x.id,x.g,x.r,x.rc];})")
        self.assertEqual(len(res), len(SC)); maxd = 0
        for i, g, r, rc in res:
            s = SC[i]
            self.assertEqual(g is None, s["global"] is None, i)
            if g is not None:
                maxd = max(maxd, abs(g - s["global"])); self.assertEqual(r, s["rang"], i); self.assertEqual(rc, s["rang_complets"], i)
        self.assertLess(maxd, 1e-5)
    def test_04_poids_recalcul_et_retour(self):
        p = self.page()
        p.evaluate("()=>__socialistometre.setWeights({A:0.25,B:0.25,C:0.25,D:0.25})")
        g = p.evaluate("()=>__socialistometre.P.filter(function(x){return x.id==='FRA'})[0].g")
        d = SC["FRA"]["dimensions"]; self.assertAlmostEqual(g, sum(d[k] for k in "ABCD") / 4, places=4)
        p.click("nav button[data-t=classement]"); self.assertIn("Pondérations modifiées", p.inner_text("#wnotice"))
        p.evaluate("()=>__socialistometre.setWeights({A:0.45,B:0.2,C:0.2,D:0.15})")
        g = p.evaluate("()=>__socialistometre.P.filter(function(x){return x.id==='FRA'})[0].g")
        self.assertAlmostEqual(g, SC["FRA"]["global"], places=4)
        self.assertEqual(self.errs, [])
    def test_05_onglets_recherche_comparaison_fiche(self):
        p = self.page()
        for t in ["comparer", "fiche", "dispersion", "distribution", "poids", "methode", "classement"]:
            p.click(f"nav button[data-t={t}]"); self.assertTrue(p.is_visible(f"#s-{t}"), t)
        p.click("nav button[data-t=classement]"); p.fill("#q", "danemark")
        self.assertIn("Danemark", p.inner_text("#tbl")); self.assertLess(p.locator("#tbl tbody tr").count(), 5)
        p.fill("#q", ""); p.click("#tbl th[data-k=g]")
        p.click("nav button[data-t=comparer]"); self.assertGreater(p.locator("#cmp table").count(), 0)
        p.click("nav button[data-t=fiche]"); self.assertIn("Brut", p.inner_text("#fiche")); self.assertIn("Fiabilité", p.inner_text("#fiche"))
        p.click("nav button[data-t=dispersion]"); self.assertGreater(p.locator("#scat circle").count(), 150)
        p.select_option("#sy", "B"); self.assertGreater(p.locator("#scat circle").count(), 20)
        p.click("nav button[data-t=distribution]"); self.assertGreater(p.locator("#hist rect").count(), 15)
        p.click("nav button[data-t=methode]"); self.assertIn("T12", p.inner_text("#meth")); self.assertIn("P01", p.inner_text("#meth"))
        self.assertEqual(self.errs, [])
    def test_06_zoom(self):
        p = self.page(); n0 = p.locator("#swarm circle").count()
        p.fill("#zmin", "60"); p.fill("#zmax", "80"); p.dispatch_event("#zmax", "change")
        self.assertLess(p.locator("#swarm circle").count(), n0); self.assertEqual(self.errs, [])
    def test_07_mobile_sans_debordement(self):
        p = self.page(375, 800); p.wait_for_selector("#swarm circle")
        self.assertLessEqual(p.evaluate("document.documentElement.scrollWidth"), 380)
        for t in ["fiche", "dispersion", "poids"]:
            p.click(f"nav button[data-t={t}]")
            self.assertLessEqual(p.evaluate("document.documentElement.scrollWidth"), 380, t)
        self.assertEqual(self.errs, [])
if __name__ == "__main__":
    unittest.main(verbosity=2)
