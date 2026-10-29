#!/usr/bin/env python3
"""Construit les données traitées à partir des extractions littérales (data/raw/*/…_extraction.csv) et du référentiel.

Sorties (data/processed/) :
  observations.csv – une ligne par (entité, source, édition, indicateur, année) : valeur officielle telle que publiée,
                     échelle officielle, valeur 0-100 (src/transform.py), métadonnées complètes de traçabilité.
  contexte.csv     – données contextuelles (aucun poids dans les coordonnées).
  anomalies.csv    – journal (valeurs hors échelle officielle, entités non classées, etc.).

Aucun rapprochement automatique : une entité source absente de data/reference/correspondances.csv fait échouer la
construction. Aucune valeur manquante n'est remplacée (ni zéro, ni estimation).
Usage : python3 -m src.build
"""
import json
import os

from src import transform as T
from src.common import PROC, RAW, REF, config, manifest, read_csv, write_csv

OBS_FIELDS = ["iso3", "source", "edition", "indicateur", "libelle", "role", "annee_reference", "periode_debut", "periode_fin",
              "valeur_officielle", "echelle_min", "echelle_max", "valeur_0_100", "transformation", "nom_dans_source",
              "rang_officiel", "statut_validation", "note", "url_source", "date_publication", "date_collecte", "sha256_source"]
CTX_FIELDS = ["iso3", "indicateur", "libelle", "unite", "annee", "valeur", "source", "url", "fichier", "date_collecte",
              "date_revision", "transformation", "limites"]
ANOM_FIELDS = ["niveau", "code", "iso3", "source", "detail"]


def corr():
    m = {}
    for r in read_csv(os.path.join(REF, "correspondances.csv")):
        key = (r["source"], r["edition"], r["code_source"] or r["nom_source"])
        assert key not in m, f"correspondance en double : {key}"
        m[key] = r["iso3"]
    return m


class Builder:
    def __init__(self):
        self.S = config("sources.json")["sources"]
        self.C = corr()
        self.pays = {p["iso3"]: p for p in read_csv(os.path.join(REF, "pays.csv"))}
        self.obs, self.anom = [], []
        self.keys = set()

    def iso(self, src, ed, key):
        k = (src, ed, key)
        if k not in self.C:
            raise SystemExit(f"ERREUR : entité « {key} » ({src}/{ed}) absente de data/reference/correspondances.csv "
                             "— exécuter tools/init_reference.py puis relire la correspondance")
        return self.C[k]

    def meta(self, src, ed, fichier):
        e = self.S[src]["editions"][ed]
        man = manifest(src)["fichiers"].get(fichier, {})
        return e, man

    def add(self, iso3, src, ed, ind, libelle, role, annee, valeur, mn, mx, nom, rang="", note="", deb="", fin="",
            fichier="", statut="extrait_verifie"):
        e, man = self.meta(src, ed, fichier)
        if valeur in (None, "", "N/A"):
            return  # absence conservée comme absence
        k = (iso3, src, ed, ind, annee)
        assert k not in self.keys, f"doublon {k}"
        self.keys.add(k)
        v100 = T.to_100(valeur, mn, mx)
        if not T.in_scale(valeur, mn, mx):
            statut = "hors_echelle_officielle"
            self.anom.append({"niveau": "info", "code": "HORS_ECHELLE", "iso3": iso3, "source": src,
                              "detail": f"{ind} {annee} = {valeur} hors de l'échelle nominale [{mn}, {mx}] ; valeur officielle conservée sans troncature"})
        self.obs.append({"iso3": iso3, "source": src, "edition": ed, "indicateur": ind, "libelle": libelle, "role": role,
                         "annee_reference": annee, "periode_debut": deb or f"{annee}-01-01", "periode_fin": fin or f"{annee}-12-31",
                         "valeur_officielle": valeur, "echelle_min": mn, "echelle_max": mx, "valeur_0_100": repr(v100),
                         "transformation": T.describe(mn, mx), "nom_dans_source": nom, "rang_officiel": rang,
                         "statut_validation": statut, "note": note, "url_source": e.get("url_source", ""),
                         "date_publication": e.get("date_publication", ""), "date_collecte": man.get("date_collecte", ""),
                         "sha256_source": man.get("sha256", "")})

    # ------------------------------------------------------------------ sources
    def fraser(self):
        S = self.S["fraser"]
        comps = {c["id"]: c for c in S["composantes"]}
        for ed, e in S["editions"].items():
            if e["statut"] != "importee":
                self.anom.append({"niveau": "avertissement", "code": "EDITION_NON_IMPORTEE", "iso3": "", "source": "fraser",
                                  "detail": f"{e['nom']} : {e.get('raison', '')}"})
                continue
            mn, mx = e["echelle"]["min"], e["echelle"]["max"]
            fichier = "efw2025.pdf" if ed == "efw2025" else f"{ed}.xlsx"
            for r in read_csv(os.path.join(RAW, e["extraction"])):
                iso3 = self.iso("fraser", ed, r["nom_source"])
                y = int(r["annee"])
                self.add(iso3, "fraser", ed, "efw_summary", "Indice synthétique EFW", "principal", y, r["summary"], mn, mx,
                         r["nom_source"], r["rang"], fichier=fichier)
                for k in range(1, 6):
                    c = comps[f"area{k}"]
                    self.add(iso3, "fraser", ed, f"area{k}", c["nom"], "composante", y, r[f"area{k}"], mn, mx, r["nom_source"],
                             r.get(f"rang{k}", ""), note=c["nom_officiel"], fichier=fichier)

    def heritage(self):
        S = self.S["heritage"]
        ed = "ief2026"
        e = S["editions"][ed]
        mn, mx = e["echelle"]["min"], e["echelle"]["max"]
        for r in read_csv(os.path.join(RAW, e["extraction"])):
            iso3 = self.iso("heritage", ed, r["nom_source"])
            y, deb, fin = e["annee_reference"], e["periode_debut"], e["periode_fin"]
            if r["score"] == "N/A":
                self.anom.append({"niveau": "info", "code": "NON_CLASSE_HERITAGE", "iso3": iso3, "source": "heritage",
                                  "detail": f"{r['nom_source']} : score global « N/A » (non classé) ; composantes publiées conservées"})
            self.add(iso3, "heritage", ed, "ief_overall", "Score global IEF", "principal", y, r["score"], mn, mx, r["nom_source"],
                     "" if r["rang_mondial"] == "N/A" else r["rang_mondial"], deb=deb, fin=fin, fichier="ief2026.pdf")
            for c in S["composantes"]:
                self.add(iso3, "heritage", ed, c["id"], c["nom"], "composante", y, r[c["id"]], mn, mx, r["nom_source"],
                         note=c["nom_officiel"], deb=deb, fin=fin, fichier="ief2026.pdf")

    def vdem(self):
        S = self.S["vdem"]
        ed = "v16"
        e = S["editions"][ed]
        mn, mx = e["echelle"]["min"], e["echelle"]["max"]
        for r in read_csv(os.path.join(RAW, e["extraction"])):
            iso3 = self.iso("vdem", ed, r["country_text_id"])
            y = int(r["year"])
            note = f"intervalle HPD 68 % : [{r['v2x_libdem_codelow']} ; {r['v2x_libdem_codehigh']}]" if r["v2x_libdem_codelow"] else ""
            self.add(iso3, "vdem", ed, "v2x_libdem", "Indice de démocratie libérale (LDI)", "principal", y, r["v2x_libdem"], mn, mx,
                     r["country_name"], note=note, fichier="vdem.RData")
            for k, lib in (("v2x_libdem_codelow", "LDI — borne basse HPD 68 %"), ("v2x_libdem_codehigh", "LDI — borne haute HPD 68 %")):
                self.add(iso3, "vdem", ed, k, lib, "incertitude", y, r[k], mn, mx, r["country_name"], fichier="vdem.RData")
            for c in S["composantes"]:
                self.add(iso3, "vdem", ed, c["id"], c["nom"], "composante", y, r[c["id"]], mn, mx, r["country_name"],
                         note=c["nom_officiel"], fichier="vdem.RData")

    def freedomhouse(self):
        S = self.S["freedomhouse"]
        cs = {c["id"]: c for c in S["composantes"]}
        for ed, fichier in (("fiw2026", "fiw2026_scores.html"), ("fiw2013_2024", "freedomhouse_fiw_2013-2024.xlsx")):
            e = S["editions"][ed]
            mn, mx = e["echelle"]["min"], e["echelle"]["max"]
            for r in read_csv(os.path.join(RAW, e["extraction"])):
                iso3 = self.iso("freedomhouse", ed, r["nom_source"])
                y = int(r["annee"])
                note = f"statut FH : {r['statut']}"
                self.add(iso3, "freedomhouse", ed, "fiw_total", "Score total Freedom in the World", "principal", y, r["total"], mn, mx,
                         r["nom_source"], note=note, fichier=fichier)
                for k in ("pr", "cl"):
                    c = cs["fiw_" + k]
                    self.add(iso3, "freedomhouse", ed, c["id"], c["nom"], "composante", y, r[k], c["echelle"]["min"],
                             c["echelle"]["max"], r["nom_source"], note=c["nom_officiel"], fichier=fichier)

    # ------------------------------------------------------------------ contexte
    def contexte(self):
        cfg = config("contexte.json")
        y0, y1 = cfg["fenetre_annees"]
        man = manifest("contexte")["fichiers"]
        rows = []
        known = set(self.pays)

        def put(ind, iso3, y, v, rev=""):
            if iso3 not in known:
                return
            m = man[ind["fichier"]]
            rows.append({"iso3": iso3, "indicateur": ind["id"], "libelle": ind["libelle"], "unite": ind["unite"], "annee": y,
                         "valeur": v, "source": ind["source"], "url": ind["url"], "fichier": ind["fichier"],
                         "date_collecte": m["date_collecte"], "date_revision": rev, "transformation": "aucune (valeur publiée)",
                         "limites": ind["limites"]})

        for ind in cfg["indicateurs"]:
            path = os.path.join(RAW, "contexte", ind["fichier"])
            best = {}
            if ind["fichier"].startswith("wb_"):
                meta, data = json.load(open(path, encoding="utf-8"))
                for d in data:
                    iso3, v = d["countryiso3code"], d["value"]
                    if v is None or not iso3:
                        continue
                    y = int(d["date"])
                    if y0 <= y <= y1 and (iso3 not in best or y > best[iso3][0]):
                        best[iso3] = (y, v)
                for iso3, (y, v) in best.items():
                    put(ind, iso3, y, v, meta.get("lastupdated", ""))
                continue
            for r in read_csv(path):
                if r["OBS_VALUE"] == "":
                    continue
                ok = {"prelevements_obligatoires": lambda r: r["SECTOR"] == "S13" and r["UNIT_MEASURE"] == "PT_B1GQ" and r["STANDARD_REVENUE"] == "_T",
                      "coin_fiscal": lambda r: r["MEASURE"] == "AV_TW" and r["HOUSEHOLD_TYPE"] == "S_C0" and r["INCOME_PRINCIPAL"] == "AW100" and r["UNIT_MEASURE"] == "PT_COS_LB",
                      "taux_marginal_ir": lambda r: r["MEASURE"] == "TS_PIT"}[ind["id"]]
                if not ok(r):
                    continue
                y, iso3 = int(r["TIME_PERIOD"]), r["REF_AREA"]
                if y0 <= y <= y1 and (iso3 not in best or y > best[iso3][0]):
                    best[iso3] = (y, float(r["OBS_VALUE"]))
            for iso3, (y, v) in best.items():
                put(ind, iso3, y, v)
        rows.sort(key=lambda r: (r["iso3"], r["indicateur"]))
        write_csv(os.path.join(PROC, "contexte.csv"), rows, CTX_FIELDS)
        return rows

    def run(self):
        self.fraser(); self.heritage(); self.vdem(); self.freedomhouse()
        self.obs.sort(key=lambda r: (r["iso3"], r["source"], r["edition"], r["indicateur"], int(r["annee_reference"])))
        write_csv(os.path.join(PROC, "observations.csv"), self.obs, OBS_FIELDS)
        ctx = self.contexte()
        self.anom.sort(key=lambda a: (a["niveau"], a["code"], a["iso3"], a["detail"]))
        write_csv(os.path.join(PROC, "anomalies.csv"), self.anom, ANOM_FIELDS)
        print(f"observations : {len(self.obs)} ; contexte : {len(ctx)} ; anomalies : {len(self.anom)}")


if __name__ == "__main__":
    Builder().run()
