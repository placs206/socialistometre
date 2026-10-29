#!/usr/bin/env python3
"""Assemble index.html (fichier autonome, hors ligne) à partir de tools/template.html et des données calculées.

Le HTML ne recalcule aucune coordonnée : il lit les scénarios produits par src/coordinates.py et les observations
officielles produites par src/build.py. Toutes les données nécessaires à l'audit sont intégrées.
Usage : python3 tools/build_html.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.common import PROC, REF, ROOT, config, p, read_csv, read_json  # noqa: E402

STAT = {"complet": 0, "x_seulement": 1, "y_seulement": 2, "aucune": 3}


def build():
    S = config("sources.json")["sources"]
    par = config("parametres.json")
    ctx_cfg = config("contexte.json")
    co = read_json(os.path.join(PROC, "coordonnees.json"))
    pays = read_csv(os.path.join(REF, "pays.csv"))

    obs = {}
    for o in read_csv(os.path.join(PROC, "observations.csv")):
        if o["source"] == "vdem" and o["role"] != "principal" and int(o["annee_reference"]) < 2020:
            continue  # allègement du HTML : composantes et intervalles V-Dem antérieurs à 2020 restent dans observations.csv
        rec = [int(o["annee_reference"]), o["valeur_officielle"], float(o["valeur_0_100"]), o["edition"], o["rang_officiel"],
               1 if o["statut_validation"] == "hors_echelle_officielle" else 0, o["note"], o["nom_dans_source"]]
        obs.setdefault(o["iso3"], {}).setdefault(o["source"], {}).setdefault(o["indicateur"], []).append(rec)

    ctx = {}
    for c in read_csv(os.path.join(PROC, "contexte.csv")):
        ctx.setdefault(c["iso3"], []).append([c["indicateur"], int(c["annee"]), float(c["valeur"])])

    def pt(r):
        return None if r is None else [r["v"], r["off"], r["ed"], r["an"], r["deb"], r["fin"], 1 if r["hors"] else 0]

    scen = {}
    for sid, s in co["scenarios"].items():
        scen[sid] = {"x": s["x"]["source"], "y": s["y"]["source"], "mode": s["mode"], "officiel": s["officiel"],
                     "comptes": s["comptes"],
                     "p": {iso: [pt(v["x"]), pt(v["y"]), v["ecart"], STAT[v["statut"]]] for iso, v in s["points"].items()}}

    sources = {}
    for k, s in S.items():
        sources[k] = {f: s[f] for f in ("organisme", "indice", "axe", "role_v2", "page_methodologie", "page_donnees", "licence",
                                        "composantes", "edition_officielle_v2")}
        sources[k]["editions"] = s["editions"]

    contest_path = p("data", "contestations", "contestations.csv")
    contest = read_csv(contest_path) if os.path.exists(contest_path) else []
    val_path = p("docs", "validation.json")
    validation = read_json(val_path) if os.path.exists(val_path) else {"tests": [], "statut": "non exécuté"}

    data = {
        "meta": {"version": par["version_methodologie"], "date_version": par["date_version"], "empreinte": co["empreinte_jeu_de_donnees"],
                 "scenario_officiel": co["scenario_officiel"], "seuil_ecart": par["seuil_ecart_annees"],
                 "seuil_div": par["seuil_divergence_points"], "regles": par["regles"], "note_seuils": par["note_seuils"],
                 "collecte": {k: sorted({f.get("date_collecte", "") for f in read_json(os.path.join(ROOT, "data", "raw", k, "MANIFEST.json"))["fichiers"].values()})
                              for k in ("fraser", "heritage", "vdem", "freedomhouse", "contexte")}},
        "sources": sources,
        "pays": [{k: q[k] for k in ("iso3", "nom_fr", "nom_en", "region", "groupe_revenu", "type", "statut_politique")} for q in pays],
        "obs": obs, "scen": scen, "div": co["divergences"],
        "ctx": ctx, "ctx_cfg": ctx_cfg,
        "anom": read_csv(os.path.join(PROC, "anomalies.csv")),
        "corr": read_csv(os.path.join(REF, "correspondances.csv")),
        "contest": contest, "validation": validation,
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("</", "<\\/")
    tpl = open(p("tools", "template.html"), encoding="utf-8").read()
    assert tpl.count("/*__DATA__*/null") == 1
    out = tpl.replace("/*__DATA__*/null", blob)
    open(p("index.html"), "w", encoding="utf-8").write(out)
    print("index.html", len(out.encode("utf-8")), "octets")


if __name__ == "__main__":
    build()
