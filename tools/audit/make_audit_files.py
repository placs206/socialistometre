#!/usr/bin/env python3
"""Produit les livrables tabulaires de l'audit (racine du dépôt) :
INDICATOR_DICTIONARY.csv, DATA_QUALITY_REPORT.csv, ANOMALIES.csv, THEORETICAL_REFERENCES.md.
Prérequis : tools/audit/diagnostic.py et tools/audit/simulate.py exécutés (data/audit/*.json)."""
import csv, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402
DIMS = "ABCD"
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))


def wcsv(name, rows, fields):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="ignore"); w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def main():
    data = S.load()
    diag = J("data/audit/diagnostic.json"); sims = J("data/audit/simulations.json")
    ov0 = S.decisions_overrides(data)
    base, params, norm = S.compute(data, overrides=ov0)
    defs = S.indicator_defs(S.apply_overrides(data, ov0))
    allind = {i["id"]: i for i in data["ind"]["indicateurs"]}
    allind.update({i["id"]: i for i in data["ind"]["alternatives_sensibilite"]})
    princ = {p["id"]: p for p in J("corpus/principes.json")["principes"]}
    decs = {d["id"]: d for d in data["decisions"]["decisions"]}
    dec_of = {}
    for d in decs.values():
        for k in d["indicateurs"]:
            dec_of.setdefault(k, []).append(d["id"])

    # ---------------------------------------------------------------- INDICATOR_DICTIONARY.csv
    F = ["id", "nom", "dimension", "statut_calcul", "niveau_preuve", "definition_operationnelle", "principes", "references_verifiees", "justification_lien",
         "valeur_recherchee", "unite", "numerateur", "denominateur", "population_couverte", "periode", "source_primaire", "source_secours", "url", "formule",
         "sens_score", "bornes", "bornes_appliquees_2023", "origine_bornes", "seuils", "poids_interne", "traitement_manquants", "regles_exclusion",
         "risques_double_comptage", "limites_comparabilite", "niveau_confiance", "couverture_n", "statut_approbation", "decisions_liees"]
    rows = []
    cov = {}
    for iso, d in data["obs"].items():
        for k in d: cov[k] = cov.get(k, 0) + 1
    for iso, d in data["alt"].items():
        for k in d: cov[k] = cov.get(k, 0) + 1
    for k, i in allind.items():
        b = i.get("bornes", {})
        refs = []
        for pid in i.get("principes", []):
            p = princ.get(pid)
            if p:
                refs += [f"{pid} : Capitalisme et liberté, chap. {r['chap']}, p. {r['page']}" for r in p["refs"]]
        rows.append({"id": k, "nom": i.get("nom", i.get("code")), "dimension": i.get("dim", allind.get(i.get("remplace") or "", {}).get("dim")),
                     "statut_calcul": "retenu (score officiel)" if k in defs else ("retenu mais exclu par décision approuvée" if k in [x["id"] for x in data["ind"]["indicateurs"]] else "candidat (hors score officiel)"),
                     "niveau_preuve": i.get("niveau_preuve"), "definition_operationnelle": i.get("definition_operationnelle"), "principes": ", ".join(i.get("principes", [])),
                     "references_verifiees": " ; ".join(refs), "justification_lien": i.get("lien"), "valeur_recherchee": i.get("valeur_recherchee"), "unite": i.get("unite"),
                     "numerateur": i.get("numerateur"), "denominateur": i.get("denominateur"), "population_couverte": i.get("population_couverte"), "periode": i.get("periode"),
                     "source_primaire": i.get("source_primaire", i.get("source")), "source_secours": i.get("source_secours"), "url": i.get("url"), "formule": i.get("formule"),
                     "sens_score": i.get("sens_score"), "bornes": json.dumps(b, ensure_ascii=False),
                     "bornes_appliquees_2023": (f"[{params[k]['bas']:.4g} ; {params[k]['haut']:.4g}]" if k in params else ""),
                     "origine_bornes": "échelle naturelle / théorique de la variable" if b.get("regle") == "fixe" else "distribution observée de l'édition (dépend de l'échantillon : l'ajout de pays modifie les bornes — voir DEC-08)",
                     "seuils": i.get("seuils"), "poids_interne": i.get("poids_interne", 1.0), "traitement_manquants": i.get("traitement_manquants"),
                     "regles_exclusion": i.get("regles_exclusion"), "risques_double_comptage": i.get("chevauchement"), "limites_comparabilite": i.get("limites"),
                     "niveau_confiance": i.get("niveau_confiance"), "couverture_n": cov.get(k, 0), "statut_approbation": i.get("statut_approbation"),
                     "decisions_liees": ", ".join(dec_of.get(k, []))})
    for e in data["ind"]["exclus"]:
        rows.append({"id": "EXCLU", "nom": e["candidat"], "statut_calcul": "exclu (V1.1)", "principes": e.get("principe") or "", "justification_lien": e["raison"]})
    wcsv("INDICATOR_DICTIONARY.csv", rows, F)

    # ---------------------------------------------------------------- DATA_QUALITY_REPORT.csv
    ext = {(r["iso3"], r["indicateur"]) for r in csv.DictReader(open(os.path.join(ROOT, "data/processed/anomalies.csv"), encoding="utf-8")) if r["code"] == "VALEUR_EXTREME"}
    q = []
    ref = data["dim"]["annee_cible"]
    for src, pool in (("officiel", data["obs"]), ("candidat", data["alt"])):
        for iso in sorted(pool):
            for k, o in sorted(pool[iso].items()):
                i = allind.get(k, {})
                n = norm.get(iso, {}).get(k)
                p = params.get(k)
                ecr = ""
                if p:
                    x = o["valeur_brute"]
                    if x < min(p["bas"], p["haut"]) - 1e-12 or x > max(p["bas"], p["haut"]) + 1e-12:
                        ecr = "valeur hors bornes : écrêtée"
                q.append({"iso3": iso, "pays": data["pays"][iso]["nom_fr"], "indicateur": k, "jeu": src, "valeur_brute": o["valeur_brute"], "unite": o.get("unite"),
                          "annee": o["annee"], "ecart_annee_cible": ref - o["annee"], "source": o["source"], "url": o["url_source"], "date_collecte": o["date_collecte"],
                          "date_revision": o["date_revision"], "transformation": o["transformation"], "valeur_normalisee": "" if n is None else round(n, 4),
                          "ecretage": ecr, "valeur_extreme_5MAD": "oui" if (iso, k) in ext else "", "statut_validation": o["statut_validation"],
                          "type_source": i.get("source_type"), "niveau_preuve": i.get("niveau_preuve"), "nature": "estimation d'un modèle de mesure (perceptions / experts)" if k in ("A4", "A5", "D1", "C4") else ("notation d'experts" if k in ("A6", "D2", "D3", "D4") else "statistique officielle"),
                          "limites_comparabilite": o["limites_comparabilite"]})
    wcsv("DATA_QUALITY_REPORT.csv", q, list(q[0].keys()))

    # ---------------------------------------------------------------- ANOMALIES.csv
    def eff(dec, opt, iso):
        r, _, _ = cache.setdefault((dec, opt), S.compute(data, overrides=S.decisions_overrides(data, {dec: opt})))
        a, b = base[iso]["global"], r[iso]["global"]
        if a is None:
            return "—"
        if b is None:
            return f"score global retiré (couverture insuffisante) ; rang {base[iso]['rang']} → —"
        return f"{a:.1f} → {b:.1f} ({b - a:+.1f}) ; rang {base[iso]['rang']} → {r[iso]['rang']}"
    cache = {}
    reco = S.scenario_recommande(data)
    rr, _, _ = S.compute(data, overrides=S.decisions_overrides(data, reco))
    def eff_reco(iso):
        a, b = base[iso]["global"], rr[iso]["global"]
        if a is None:
            return "—"
        return "retiré du classement" if b is None else f"{a:.1f} → {b:.1f} ({b - a:+.1f}) ; rang {base[iso]['rang']} → {rr[iso]['rang']}"
    err = diag["erreur_sous_ensembles"]
    an = []; n = 0
    def add(**k):
        nonlocal n; n += 1
        k["id"] = f"AN-{n:04d}"; k["effet_scenario_recommande"] = eff_reco(k["iso3"]) if k.get("iso3") in base else "—"
        an.append(k)
    W = S.dim_weights(data)
    for iso, r in sorted(base.items()):
        if r["global"] is None:
            continue
        nom = data["pays"][iso]["nom_fr"]; g = r["global"]
        obs = data["obs"].get(iso, {})
        for d in DIMS:
            if r["n"][d] == 1 and r["dims"][d] is not None:
                k = next(x for x in r["norm"] if x in defs and defs[x]["dim"] == d)
                e = err.get(d, {}).get("par_k", {}).get("1", {})
                add(categorie="couverture : dimension calculée sur 1 indicateur", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule=f"{k} (seul indicateur de {d})",
                    valeur_brute=obs[k]["valeur_brute"], source=obs[k]["source"], transformation=f"{defs[k]['bornes']['regle']} → {r['norm'][k]:.1f}",
                    contribution=round(r["contributions"].get(k, 0), 2),
                    cause=f"La dimension {d} ({r['dims'][d]:.1f}) est égale à la valeur d'un seul indicateur ; erreur médiane d'une dimension à 1 indicateur : {e.get('mediane')} pts (P90 {e.get('p90')}).",
                    correction_proposee="DEC-01 (minimum d'indicateurs par dimension)", effet_correction=eff("DEC-01", "A3_B3_C2_D2", iso), certitude="élevée (fragilité démontrée sur les pays complets)", type_anomalie="fragilité méthodologique")
        nd = len(r["disponibles"])
        if nd == 2:
            add(categorie="couverture : score global sur 2 dimensions", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule="score global (poids renormalisés)",
                valeur_brute="", source="", transformation="Σ w_d·S_d / Σ w_d sur " + "+".join(r["disponibles"]), contribution="",
                cause="Score global sur 2 dimensions : erreur médiane 5,4 pts (P90 15,3) par rapport à un score complet.",
                correction_proposee="DEC-02 (3 dimensions minimum)", effet_correction=eff("DEC-02", "3_dimensions", iso), certitude="élevée", type_anomalie="fragilité méthodologique")
        obs = dict(obs); obs.update(data["alt"].get(iso, {}))
        for k, v in r["norm"].items():
            if k not in defs:
                continue
            p = params[k]; x = obs[k]["valeur_brute"]
            if (x < min(p["bas"], p["haut"]) or x > max(p["bas"], p["haut"])) and r["n"][defs[k]["dim"]] <= 2 and abs(r["contributions"].get(k, 0)) >= 10 and defs[k]["bornes"]["regle"] == "percentile":
                add(categorie="valeur écrêtée dominant une dimension peu couverte", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule=k,
                    valeur_brute=x, source=obs[k]["source"], transformation=f"P5–P95 [{p['bas']:.4g} ; {p['haut']:.4g}] → {v:.0f}", contribution=round(r["contributions"][k], 2),
                    cause=f"Valeur hors des bornes percentiles ramenée à {v:.0f}, dans une dimension à {r['n'][defs[k]['dim']]} indicateur(s).",
                    correction_proposee="DEC-01 ; DEC-08 (bornes figées)", effet_correction=eff("DEC-01", "A3_B3_C2_D2", iso), certitude="élevée", type_anomalie="fragilité méthodologique")
        if "C2" in r["norm"]:
            e2 = eff("DEC-03", "retirer", iso); rC = cache[("DEC-03", "retirer")][0][iso]["global"]
            if rC is not None and abs(rC - g) > 5:
                add(categorie="proxy faible C2 influent", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule="C2",
                    valeur_brute=obs["C2"]["valeur_brute"], source=obs["C2"]["source"], transformation=f"P5–P95 → {r['norm']['C2']:.1f}", contribution=round(r["contributions"].get("C2", 0), 2),
                    cause="C2 mesure la fourniture privée et non le financement ni le choix (P07/P08) ; niveau 3. Son retrait change le score de plus de 5 points.",
                    correction_proposee="DEC-03", effet_correction=e2, certitude="moyenne (interprétation)", type_anomalie="conceptuelle")
        if "B5" in r["norm"] and "B6" in r["norm"]:
            e5 = eff("DEC-05", "B5n", iso); r5 = cache[("DEC-05", "B5n")][0][iso]["global"]
            if r5 is not None and abs(r5 - g) > 3:
                add(categorie="double comptage B5 ⊃ B6", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule="B5 et B6",
                    valeur_brute=f"B5 {obs['B5']['valeur_brute']} ; B6 {obs['B6']['valeur_brute']}", source=obs["B5"]["source"], transformation=f"B5 → {r['norm']['B5']:.1f} ; B6 → {r['norm']['B6']:.1f}",
                    contribution=round(r["contributions"].get("B5", 0) + r["contributions"].get("B6", 0), 2),
                    cause="Les prélèvements sur le travail sont comptés dans B5 et dans B6.", correction_proposee="DEC-05", effet_correction=e5, certitude="démontrée (identité comptable)", type_anomalie="mathématique")
        if "D2" in obs and obs["D2"]["valeur_brute"] < 0:
            add(categorie="borne D2 contraire à la règle écrite", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule="D2",
                valeur_brute=obs["D2"]["valeur_brute"], source=obs["D2"]["source"], transformation="bornes 0–40 → 0", contribution=round(r["contributions"].get("D2", 0), 2),
                cause="Valeur négative de l'échelle Freedom House (−4 à 40) écrêtée à 0.", correction_proposee="DEC-06", effet_correction=eff("DEC-06", "echelle_naturelle", iso), certitude="démontrée", type_anomalie="définition")
        dm = diag["dominance"]["par_pays"].get(iso, {})
        if dm.get("delta") is not None and abs(dm["delta"]) > 10:
            k = dm["indicateur"]
            add(categorie="score dominé par un seul indicateur", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule=k,
                valeur_brute=obs[k]["valeur_brute"], source=obs[k]["source"], transformation=f"→ {r['norm'][k]:.1f}", contribution=round(r["contributions"].get(k, 0), 2),
                cause=f"Retirer le seul indicateur {k} change le score global de {dm['delta']:+.1f} points.", correction_proposee="DEC-01 / DEC-02", effet_correction=eff("DEC-01", "A3_B3_C2_D2", iso), certitude="élevée", type_anomalie="fragilité méthodologique")
        ds = [r["dims"][d] for d in DIMS if r["dims"][d] is not None]
        if len(ds) >= 2 and max(ds) - min(ds) > 70:
            hi = max((d for d in DIMS if r["dims"][d] is not None), key=lambda d: r["dims"][d]); lo = min((d for d in DIMS if r["dims"][d] is not None), key=lambda d: r["dims"][d])
            add(categorie="compensation entre dimensions", iso3=iso, pays=nom, score_actuel=round(g, 2), rang_actuel=r["rang"], indicateur_ou_formule=f"dimensions {hi} et {lo}",
                valeur_brute="", source="", transformation=f"{hi} = {r['dims'][hi]:.1f} ; {lo} = {r['dims'][lo]:.1f}", contribution="",
                cause=f"Écart de {max(ds) - min(ds):.0f} points entre dimensions : la moyenne pondérée masque des profils opposés.",
                correction_proposee="aucune correction du score (pondérations inchangées) ; affichage des contributions et des écarts dans la fiche", effet_correction="—", certitude="démontrée (constat)", type_anomalie="compensation")
    # capacité fiscale (diagnostic)
    vp = os.path.join(ROOT, "data/raw/vdem_extrait.csv")
    fc = {}
    for x in csv.DictReader(open(vp, encoding="utf-8")):
        if x["year"].startswith("2023") and x["v2stfisccap"] not in ("", "NA"):
            fc[x["country_text_id"]] = float(x["v2stfisccap"])
    import statistics
    med_fc = statistics.median(fc.values())
    for iso, r in sorted(base.items()):
        if r["global"] is None or iso not in fc:
            continue
        hi = [k for k in ("B5", "B6") if r["norm"].get(k, 0) >= 80]
        if hi and fc[iso] < 0.5:
            obs = data["obs"][iso]
            add(categorie="prélèvements faibles et faible capacité fiscale", iso3=iso, pays=data["pays"][iso]["nom_fr"], score_actuel=round(r["global"], 2), rang_actuel=r["rang"],
                indicateur_ou_formule=", ".join(hi), valeur_brute=" ; ".join(f"{k} {obs[k]['valeur_brute']}" for k in hi), source=obs[hi[0]]["source"],
                transformation=" ; ".join(f"{k} → {r['norm'][k]:.0f}" for k in hi), contribution=round(sum(r["contributions"].get(k, 0) for k in hi), 2),
                cause=f"Capacité fiscale V-Dem (v2stfisccap 2023) = {fc[iso]:.2f} (médiane mondiale {med_fc:.2f}) : le faible niveau de prélèvement peut traduire une incapacité à lever l'impôt plutôt qu'un choix.",
                correction_proposee="DEC-09 (choix normatif ; recommandation : signaler sans modifier le score)", effet_correction=eff("DEC-09", "exclure_B5_B6", iso) + " (option « retirer B5/B6 »)",
                certitude="moyenne (interprétation)", type_anomalie="conceptuelle")
    if "CHL" in base:
        r = base["CHL"]; o = data["obs"]["CHL"]
        add(categorie="cotisations obligatoires à des fonds privés non comptées", iso3="CHL", pays="Chili", score_actuel=round(r["global"], 2), rang_actuel=r["rang"], indicateur_ou_formule="B6, B7",
            valeur_brute=f"B6 {o['B6']['valeur_brute']} ; B7 {o['B7']['valeur_brute']}", source=o["B7"]["source"], transformation=f"B6 → {r['norm']['B6']:.1f} ; B7 → {r['norm']['B7']:.1f}",
            contribution=round(r["contributions"].get("B6", 0) + r["contributions"].get("B7", 0), 2),
            cause="Les cotisations retraite obligatoires versées aux AFP privées ne sont pas des impôts au sens de l'OCDE ; Friedman critique pourtant l'épargne-retraite obligatoire (P09).",
            correction_proposee="DEC-10 (source à trouver ; aucune estimation)", effet_correction="non calculable sans donnée", certitude="élevée sur le constat, effet inconnu", type_anomalie="définition / donnée manquante")
    # entités qui se recouvrent
    over = {"PSE": ["X-GAZ", "X-WBK"], "CHN": ["X-TIB", "HKG", "MAC"], "UKR": ["X-CRM", "X-DON"], "GEO": ["X-ABK", "X-OSS"], "MDA": ["X-TRN"], "CYP": ["X-NCY"],
            "SOM": ["X-SML"], "IND": ["X-KAI"], "PAK": ["X-KAP"], "AZE": ["X-NKR"], "MAR": ["X-ESH"]}
    for a, bs in over.items():
        for b in bs:
            if a in base and b in base:
                add(categorie="entités qui se recouvrent", iso3=b, pays=data["pays"][b]["nom_fr"], score_actuel=None if base[b]["global"] is None else round(base[b]["global"], 2),
                    rang_actuel=base[b]["rang"], indicateur_ou_formule="référentiel", valeur_brute="", source="Freedom House / Banque mondiale", transformation="", contribution="",
                    cause=f"Le territoire est aussi couvert, selon la source, par l'entité {data['pays'][a]['nom_fr']} ({a}) ; les classements ne sont pas additifs.",
                    correction_proposee="information (statut affiché) ; avec DEC-01, la plupart de ces entités n'ont plus de score global", effet_correction=eff("DEC-01", "A3_B3_C2_D2", b) if base[b]["global"] is not None else "—",
                    certitude="démontrée (constat)", type_anomalie="correspondance entre pays")
    FA = ["id", "type_anomalie", "categorie", "iso3", "pays", "score_actuel", "rang_actuel", "indicateur_ou_formule", "valeur_brute", "source", "transformation", "contribution",
          "cause", "correction_proposee", "effet_correction", "effet_scenario_recommande", "certitude"]
    wcsv("ANOMALIES.csv", an, FA)
    summ = {}
    for a in an:
        summ[a["categorie"]] = summ.get(a["categorie"], 0) + 1
    json.dump({"n": len(an), "par_categorie": summ, "n_pays": len({a['iso3'] for a in an})}, open(os.path.join(ROOT, "data/audit/anomalies_resume.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # ---------------------------------------------------------------- THEORETICAL_REFERENCES.md
    bib = J("corpus/bibliographie.json")
    L = ["# Références théoriques — Milton Friedman", "", "Généré par `tools/audit/make_audit_files.py` à partir de `corpus/principes.json` (citations vérifiées automatiquement contre le texte, `tools/verify_citations.py`).", ""]
    for c in bib["corpus_autorise"]:
        L += [f"**Corpus autorisé : {c['titre']}** ({c['titre_original']}, {c['edition_originale']}). Édition utilisée : {c['edition_utilisee']}. Statut : {c['statut_verification']}. Limites : {c['limites']}", ""]
    for c in bib.get("ouvrages_non_utilises", []):
        L += [f"**Non utilisé : {c['titre']}** : {c['statut']}. {c['raison']}", ""]
    L += ["Aucun indicateur statistique ni aucun seuil n'est attribué à Friedman : les indicateurs sont des choix de mesure du projet, rattachés à un principe.", "",
          "| Principe | Énoncé | Références (chap., page imprimée) | Indicateurs rattachés |", "|---|---|---|---|"]
    rat = {}
    for k, i in allind.items():
        for pid in i.get("principes", []):
            rat.setdefault(pid, []).append(k + ("" if k in defs else " (candidat)"))
    for pid, p in princ.items():
        L.append(f"| {pid} | {p['nom']} | " + " ; ".join(f"chap. {r['chap']}, p. {r['page']}" for r in p["refs"]) + f" | {', '.join(rat.get(pid, [])) or '— (aucun indicateur : principe non mesuré)'} |")
    L += ["", "## Citations", ""]
    for pid, p in princ.items():
        L.append(f"### {pid} — {p['nom']}")
        L += [f"> « {r['citation']} » — chap. {r['chap']}, p. {r['page']}" for r in p["refs"]] + [""]
    open(os.path.join(ROOT, "THEORETICAL_REFERENCES.md"), "w", encoding="utf-8").write("\n".join(L))
    print("INDICATOR_DICTIONARY.csv", len(rows), "| DATA_QUALITY_REPORT.csv", len(q), "| ANOMALIES.csv", len(an), summ)


if __name__ == "__main__":
    main()
