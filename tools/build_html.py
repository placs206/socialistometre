#!/usr/bin/env python3
"""Assemble dist/socialistometre.html (fichier autonome) à partir de tools/template.html et des données du dépôt.

Le fichier embarque : valeurs brutes (indicateurs retenus et candidats), configuration de base, registre des décisions,
résumés des simulations et du diagnostic d'audit, anomalies par pays. Les scores sont recalculés dans le navigateur par un
moteur JavaScript identique à engine/scoring.py (parité vérifiée par tests/test_html.py)."""
import csv, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402
L = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
KEEP = ("id", "dim", "nom", "unite", "orientation", "principes", "source", "source_type", "url", "bornes", "lien", "limites", "chevauchement",
        "inclus", "poids_interne", "niveau_preuve", "definition_operationnelle", "formule", "statut_approbation", "remplace")


def build():
    data = S.load()
    sc, dm, ind, pr, bib = L("data/processed/scores.json"), L("config/dimensions.json"), L("config/indicateurs.json"), L("corpus/principes.json"), L("corpus/bibliographie.json")
    stab = L("data/processed/stabilite.json")["intervalles"]
    rob = L("docs/robustesse.json")
    sims = L("data/audit/simulations.json"); diag = L("data/audit/diagnostic.json"); ares = L("data/audit/anomalies_resume.json")
    anom = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "ANOMALIES.csv"), encoding="utf-8")):
        anom.setdefault(r["iso3"], []).append({"categorie": r["categorie"], "cause": r["cause"], "correction": r["correction_proposee"], "effet": r["effet_correction"], "certitude": r["certitude"]})
    byid = {i["id"]: i for i in ind["indicateurs"]}
    inds = []
    for i in ind["indicateurs"]:
        x = {k: i[k] for k in KEEP if k in i}; x["candidat"] = False; inds.append(x)
    for a in ind["alternatives_sensibilite"]:
        x = {k: a[k] for k in KEEP if k in a}; x["candidat"] = True
        if a.get("remplace") in byid:
            base = byid[a["remplace"]]
            for k in ("dim", "unite", "principes", "source", "source_type", "lien", "limites", "chevauchement"):
                x.setdefault(k, base.get(k))
        x.setdefault("nom", a.get("definition_operationnelle", a["id"])); x.setdefault("url", "https://data.worldbank.org/indicator/" + a.get("serie", ""))
        x.setdefault("principes", []); x.setdefault("lien", ""); x.setdefault("limites", ""); x.setdefault("source_type", "intergouvernementale")
        inds.append(x)
    sens = sims["sensibilite_methodologique"]["pays"]
    pays = []
    for iso, p in sc["pays"].items():
        raw = {}
        for pool in (data["obs"], data["alt"]):
            for k, o in pool.get(iso, {}).items():
                raw[k] = [o["valeur_brute"], o["annee"], o["statut_validation"], o["date_revision"], o["limites_comparabilite"]]
        pays.append({"id": iso, "nom": p["nom"], "nom_en": p["nom_en"], "region": p["region"], "revenu": p["groupe_revenu"], "type": p["type"],
                     "statut_pol": p["statut_politique"], "fiab": p["fiabilite"], "avert": p["avertissements"], "stab": stab.get(iso),
                     "sens": sens.get(iso), "anom": anom.get(iso, []), "raw": raw})
    pays.sort(key=lambda x: x["nom"])
    simsum = {}
    for d, opts in sims["decisions"].items():
        simsum[d] = {o: {k: v[k] for k in ("n_global_avant", "n_global_apres", "n_global_retires", "n_global_ajoutes", "spearman_rangs_communs",
                                           "variation_absolue_moyenne", "variation_absolue_max", "n_variation_sup_5")} | {"plus_fortes_variations": [{"pays": x["pays"], "variation": x["variation"]} for x in v["plus_fortes_variations"][:5]]}
                     for o, v in opts.items()}
    decisions = [{k: d.get(k) for k in ("id", "titre", "categorie", "categorie_libelle", "nature", "indicateurs", "pays_concernes", "fait_observe", "regle_actuelle",
                                         "probleme", "proposition", "justification_quantitative", "options", "option_recommandee", "statut", "option_retenue", "date_decision")}
                 for d in data["decisions"]["decisions"]]
    out = {"meta": {"version": dm["version_methodologie"], "annee": sc["annee_cible"], "hash": sc["empreinte_jeu_de_donnees"], "n": sc["n_entites"],
                    "n_score": sc["n_avec_score_global"], "collecte": L("data/raw/MANIFEST.json")["genere_le"], "regle": dm["regle_score_global"],
                    "fiabilite_cfg": dm["fiabilite"], "qualite_source": dm["qualite_source"]},
           "dimensions": dm["dimensions"], "regles_base": S.rules_of(data), "indicateurs": inds, "decisions": decisions, "simulations": simsum,
           "diagnostic": {"erreur_sous_ensembles": diag["erreur_sous_ensembles"], "saturation": diag["saturation"]}, "anomalies_resume": ares,
           "exclus": ind["exclus"], "principes": pr["principes"], "livre": bib["corpus_autorise"], "tests": rob["tests"], "pays": pays}
    blob = json.dumps(out, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = open(os.path.join(ROOT, "tools", "template.html"), encoding="utf-8").read()
    html = tpl.replace("/*__DATA__*/null", blob)
    assert html != tpl
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    open(os.path.join(ROOT, "dist", "socialistometre.html"), "w", encoding="utf-8").write(html)
    print("dist/socialistometre.html", len(html), "octets")


if __name__ == "__main__":
    build()
