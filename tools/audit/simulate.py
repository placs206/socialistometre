#!/usr/bin/env python3
"""Simulations avant/après des décisions du registre (config/decisions.json) → data/audit/simulations.json,
data/audit/avant_apres_scenario_recommande.csv et DECISION_REGISTER.csv (racine du dépôt).

Pour chaque option de chaque décision : scores recalculés (méthode officielle + cette seule option), comparés à la méthode officielle.
Scénario recommandé : méthode officielle + option recommandée de chaque décision non tranchée.
Attribution d'une variation : dimension et indicateur dont la contribution au score global varie le plus (en valeur absolue).
"""
import csv, hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402
DIMS = "ABCD"


def contrib_dims(r, ind_dim):
    out = {d: 0.0 for d in DIMS}
    for k, v in r["contributions"].items():
        out[ind_dim.get(k, k[0])] += v
    return out


def comparer(data, base, alt, ov_alt):
    d_alt = S.apply_overrides(data, ov_alt)
    ind_dim = {i["id"]: i["dim"] for i in d_alt["ind"]["indicateurs"]}
    ind_dim.update({i["id"]: i["dim"] for i in data["ind"]["indicateurs"]})
    g0 = {k: v["global"] for k, v in base.items() if v["global"] is not None}
    g1 = {k: v["global"] for k, v in alt.items() if v["global"] is not None}
    com = sorted(k for k in g0 if k in g1)
    rows = []
    for k in sorted(set(g0) | set(g1)):
        a, b = g0.get(k), g1.get(k)
        row = {"iso3": k, "pays": data["pays"][k]["nom_fr"], "ancien_score": None if a is None else round(a, 2), "nouveau_score": None if b is None else round(b, 2),
               "variation": None if a is None or b is None else round(b - a, 2), "ancien_rang": base[k]["rang"], "nouveau_rang": alt[k]["rang"],
               "variation_rang": None if a is None or b is None else base[k]["rang"] - alt[k]["rang"]}
        c0, c1 = contrib_dims(base[k], ind_dim), contrib_dims(alt[k], ind_dim)
        dd = {d: c1[d] - c0[d] for d in DIMS}
        di = {i: alt[k]["contributions"].get(i, 0) - base[k]["contributions"].get(i, 0) for i in set(alt[k]["contributions"]) | set(base[k]["contributions"])}
        row["dimension_responsable"] = max(dd, key=lambda d: abs(dd[d])) if a is not None and b is not None else ""
        row["indicateur_responsable"] = max(di, key=lambda i: abs(di[i])) if di and a is not None and b is not None else ""
        expl = []
        for d in DIMS:
            if (base[k]["dims"][d] is None) != (alt[k]["dims"][d] is None):
                expl.append(f"dimension {d} {'retirée' if alt[k]['dims'][d] is None else 'ajoutée'} ({alt[k]['n'][d]} indicateur(s))")
            elif base[k]["dims"][d] is not None and abs(alt[k]["dims"][d] - base[k]["dims"][d]) > 0.05:
                expl.append(f"{d} {base[k]['dims'][d]:.1f}→{alt[k]['dims'][d]:.1f}")
        if a is not None and b is None:
            expl.append("score global retiré (couverture insuffisante)")
        if a is None and b is not None:
            expl.append("score global ajouté")
        if row["indicateur_responsable"]:
            i = row["indicateur_responsable"]
            expl.append(f"contribution de {i} : {base[k]['contributions'].get(i, 0):.1f} → {alt[k]['contributions'].get(i, 0):.1f} pts")
        row["explication"] = " ; ".join(expl)
        rows.append(row)
    rho = S.spearman([g0[k] for k in com], [g1[k] for k in com]) if len(com) > 2 else None
    mv = sorted((r for r in rows if r["variation"] is not None), key=lambda r: -abs(r["variation"]))
    return {"n_global_avant": len(g0), "n_global_apres": len(g1), "n_global_retires": sum(1 for k in g0 if k not in g1),
            "n_global_ajoutes": sum(1 for k in g1 if k not in g0), "spearman_rangs_communs": None if rho is None else round(rho, 4),
            "variation_absolue_moyenne": round(sum(abs(r["variation"]) for r in mv) / len(mv), 2) if mv else 0,
            "variation_absolue_max": round(abs(mv[0]["variation"]), 2) if mv else 0,
            "n_variation_sup_5": sum(1 for r in mv if abs(r["variation"]) > 5),
            "plus_fortes_variations": [{k: r[k] for k in ("iso3", "pays", "ancien_score", "nouveau_score", "variation", "ancien_rang", "nouveau_rang", "explication")} for r in mv[:10]],
            "retires": [r["pays"] for r in rows if r["ancien_score"] is not None and r["nouveau_score"] is None]}, rows


def main():
    data = S.load()
    ov0 = S.decisions_overrides(data)
    base, _, _ = S.compute(data, overrides=ov0)
    sims = {"methode_officielle": {"decisions_approuvees": {d["id"]: d.get("option_retenue") for d in data["decisions"]["decisions"] if d.get("statut") == "approuvée"}},
            "decisions": {}}
    for dcs in data["decisions"]["decisions"]:
        sims["decisions"][dcs["id"]] = {}
        for o in dcs["options"]:
            ch = {dcs["id"]: o["id"]}
            ov = S.decisions_overrides(data, ch)
            alt, _, _ = S.compute(data, overrides=ov)
            sims["decisions"][dcs["id"]][o["id"]], _ = comparer(data, base, alt, ov)
    reco = S.scenario_recommande(data)
    ov = S.decisions_overrides(data, reco)
    alt, _, _ = S.compute(data, overrides=ov)
    sims["scenario_recommande"], rows = comparer(data, base, alt, ov)
    sims["scenario_recommande"]["choix"] = reco
    # sensibilité : pays dont le score varie le plus selon les options (étendue sur toutes les options testées isolément + scénario)
    spread = {}
    for dcs in data["decisions"]["decisions"]:
        for o in dcs["options"]:
            alt_o, _, _ = S.compute(data, overrides=S.decisions_overrides(data, {dcs["id"]: o["id"]}))
            for k, r in alt_o.items():
                if r["global"] is not None:
                    spread.setdefault(k, []).append(r["global"])
    for k, r in alt.items():
        if r["global"] is not None:
            spread.setdefault(k, []).append(r["global"])
    sens = sorted(((max(v) - min(v), k) for k, v in spread.items() if len(v) > 1), reverse=True)
    sims["sensibilite_methodologique"] = {"definition": "étendue (max − min) du score global sur toutes les options du registre testées une à une et sur le scénario recommandé ; ce n'est PAS un intervalle de confiance",
                                          "seuil_signalement": 10, "n_pays_sensibles": sum(1 for s, _ in sens if s > 10),
                                          "pays": {k: round(s, 2) for s, k in sens}}
    os.makedirs(os.path.join(ROOT, "data/audit"), exist_ok=True)
    json.dump(sims, open(os.path.join(ROOT, "data/audit/simulations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    with open(os.path.join(ROOT, "data/audit/avant_apres_scenario_recommande.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n"); w.writeheader()
        for r in sorted(rows, key=lambda r: (r["nouveau_rang"] or 999, r["iso3"])):
            w.writerow(r)
    # registre au format CSV
    cfg_hash = hashlib.sha256(json.dumps(data["decisions"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    with open(os.path.join(ROOT, "DECISION_REGISTER.csv"), "w", encoding="utf-8", newline="") as f:
        fields = ["id", "titre", "categorie", "categorie_libelle", "nature", "indicateurs", "pays_concernes", "fait_observe", "regle_actuelle", "probleme",
                  "proposition", "option_recommandee", "options", "justification_quantitative", "consequences_option_recommandee", "statut", "option_retenue",
                  "decision_utilisateur", "commentaire_utilisateur", "date_proposition", "date_decision", "version_methode", "empreinte_configuration", "empreinte_registre"]
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for d in data["decisions"]["decisions"]:
            s = sims["decisions"][d["id"]][d["option_recommandee"]]
            cons = (f"{s['n_global_apres']} scores globaux (avant {s['n_global_avant']}) ; Spearman {s['spearman_rangs_communs']} ; variation moyenne {s['variation_absolue_moyenne']} pts, "
                    f"max {s['variation_absolue_max']} pts ; " + ", ".join(f"{x['pays']} {x['variation']:+.1f}" for x in s["plus_fortes_variations"][:4]))
            row = {k: d.get(k) for k in fields}
            row.update({"indicateurs": ", ".join(d["indicateurs"]), "options": " | ".join(f"{o['id']} : {o['libelle']}" for o in d["options"]),
                        "consequences_option_recommandee": cons, "empreinte_registre": cfg_hash})
            w.writerow(row)
    sr = sims["scenario_recommande"]
    print(f"scénario recommandé : {sr['n_global_apres']} scores (avant {sr['n_global_avant']}), Spearman {sr['spearman_rangs_communs']}, var. moy {sr['variation_absolue_moyenne']}")
    for d, opts in sims["decisions"].items():
        print(d, {o: (v["n_global_apres"], v["spearman_rangs_communs"], v["variation_absolue_max"]) for o, v in opts.items()})
    print("pays méthodologiquement sensibles (>10 pts) :", sims["sensibilite_methodologique"]["n_pays_sensibles"])


if __name__ == "__main__":
    main()
