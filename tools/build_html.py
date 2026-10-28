#!/usr/bin/env python3
"""Assemble dist/socialistometre.html (fichier autonome) à partir de tools/template.html et des données calculées."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))

def build():
    sc, dm, ind, pr, bib = L("data/processed/scores.json"), L("config/dimensions.json"), L("config/indicateurs.json"), L("corpus/principes.json"), L("corpus/bibliographie.json")
    stab = L("data/processed/stabilite.json")["intervalles"]
    rob = L("docs/robustesse.json")
    pays = []
    for iso, p in sc["pays"].items():
        pays.append({"id": iso, "nom": p["nom"], "nom_en": p["nom_en"], "region": p["region"], "revenu": p["groupe_revenu"], "type": p["type"],
                     "statut_pol": p["statut_politique"], "dims": p["dimensions"], "global": p["global"], "rang": p["rang"], "rang_c": p["rang_complets"],
                     "couv": p["statut_couverture"], "absentes": p["dimensions_absentes"], "n_dim": p["n_par_dimension"], "fiab": p["fiabilite"],
                     "avert": p["avertissements"], "stab": stab.get(iso),
                     "ind": {k: [v["brut"], v["norm"], v["annee"], v["statut"], v["revision"], v["limites"]] for k, v in p["indicateurs"].items()}})
    pays.sort(key=lambda x: x["nom"])
    data = {"meta": {"version": dm["version_methodologie"], "annee": sc["annee_cible"], "hash": sc["empreinte_jeu_de_donnees"], "n": sc["n_entites"],
                     "n_score": sc["n_avec_score_global"], "collecte": L("data/raw/MANIFEST.json")["genere_le"], "regle": dm["regle_score_global"],
                     "fiabilite_cfg": dm["fiabilite"], "qualite_source": dm["qualite_source"]},
            "dimensions": dm["dimensions"],
            "indicateurs": [{k: i[k] for k in ("id", "dim", "nom", "unite", "orientation", "principes", "source", "source_type", "url", "bornes", "lien", "limites", "chevauchement")} for i in ind["indicateurs"]],
            "normalisation": sc["normalisation"]["parametres"] if "parametres" in sc["normalisation"] else {},
            "exclus": ind["exclus"], "principes": pr["principes"], "livre": bib["corpus_autorise"], "tests": rob["tests"], "pays": pays}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = open(os.path.join(ROOT, "tools", "template.html"), encoding="utf-8").read()
    out = tpl.replace("/*__DATA__*/null", blob)
    assert out != tpl
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    open(os.path.join(ROOT, "dist", "socialistometre.html"), "w", encoding="utf-8").write(out)
    print("dist/socialistometre.html", len(out), "octets")

if __name__ == "__main__":
    build()
