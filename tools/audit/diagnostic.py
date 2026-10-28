#!/usr/bin/env python3
"""Diagnostic quantitatif de la méthode officielle (audit) → data/audit/diagnostic.json.

Mesures (toutes déterministes) :
  couverture        : nombre d'indicateurs par dimension et par pays ; dimensions calculées sur 1 seul indicateur
  erreur_sous_ensembles : erreur commise sur un score de dimension calculé avec k indicateurs au lieu de tous
                      (pays disposant de tous les indicateurs de la dimension ; tous les sous-ensembles de taille k)
  saturation        : part des valeurs normalisées exactement à 0 ou à 100 (effet des bornes)
  biais_revenu      : moyenne des scores normalisés par groupe de revenu (Banque mondiale)
  capacite_fiscale  : corrélation (Spearman) des indicateurs B5/B6/C3 avec la capacité fiscale V-Dem (v2stfisccap) et l'état de droit (A4)
  correlations      : matrice de Spearman entre indicateurs (paires avec n ≥ 20)
  compensation      : écart max-min entre dimensions par pays
  dominance         : variation du score global quand on retire un seul indicateur du pays (pays sensibles à un indicateur)
"""
import csv, itertools, json, os, statistics, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402

DIMS = "ABCD"


def main():
    data = S.load()
    ov = S.decisions_overrides(data)
    res, params, norm = S.compute(data, overrides=ov)
    d_eff = S.apply_overrides(data, ov)
    defs = S.indicator_defs(d_eff); ind_dim = {k: v["dim"] for k, v in defs.items()}
    W = S.dim_weights(d_eff)
    pays = data["pays"]
    ranked = [k for k, r in res.items() if r["global"] is not None]
    out = {"methode": "officielle", "decisions_appliquees": sorted(d["id"] for d in data["decisions"].get("decisions", []) if d.get("statut") == "approuvée")}

    # couverture
    one = {d: sorted(k for k in ranked if res[k]["n"][d] == 1) for d in DIMS}
    out["couverture"] = {
        "n_score_global": len(ranked),
        "n_global_avec_dimension_a_1_indicateur": sum(1 for k in ranked if any(res[k]["n"][d] == 1 for d in DIMS)),
        "dimension_a_1_indicateur": {d: len(v) for d, v in one.items()},
        "exemples_A_1_indicateur": one["A"],
        "n_indicateurs_par_dimension": {d: sum(1 for k in defs if ind_dim[k] == d) for d in DIMS},
        "repartition_nA": {str(n): sum(1 for k in ranked if res[k]["n"]["A"] == n) for n in range(0, 7)},
    }

    # erreur des sous-ensembles
    err = {}
    for d in DIMS:
        ks = sorted(k for k in defs if ind_dim[k] == d)
        full = [c for c in pays if all(k in norm.get(c, {}) for k in ks)]
        if len(full) < 10:
            continue
        err[d] = {"n_pays_complets": len(full), "n_indicateurs": len(ks), "par_k": {}}
        for k in range(1, len(ks)):
            e = []
            for sub in itertools.combinations(ks, k):
                for c in full:
                    ref = sum(norm[c][i] for i in ks) / len(ks)
                    e.append(abs(sum(norm[c][i] for i in sub) / k - ref))
            e.sort()
            err[d]["par_k"][str(k)] = {"mediane": round(statistics.median(e), 2), "p90": round(e[int(0.9 * len(e))], 2), "max": round(e[-1], 2)}
    out["erreur_sous_ensembles"] = err

    # saturation
    out["saturation"] = {}
    for k in sorted(defs):
        v = [norm[c][k] for c in norm if k in norm[c]]
        out["saturation"][k] = {"n": len(v), "a_0": sum(1 for x in v if x <= 1e-9), "a_100": sum(1 for x in v if x >= 100 - 1e-9),
                                "bornes": [params[k]["bas"], params[k]["haut"]], "regle": defs[k]["bornes"]["regle"]}

    # biais revenu
    groups = ["Revenu faible", "Revenu intermédiaire inférieur", "Revenu intermédiaire supérieur", "Revenu élevé"]
    bias = {}
    for k in sorted(defs) + list(DIMS) + ["G"]:
        bias[k] = {}
        for g in groups:
            if k in DIMS:
                v = [res[c]["dims"][k] for c in pays if pays[c]["groupe_revenu"] == g and res[c]["dims"][k] is not None]
            elif k == "G":
                v = [res[c]["global"] for c in pays if pays[c]["groupe_revenu"] == g and res[c]["global"] is not None]
            else:
                v = [norm[c][k] for c in pays if pays[c]["groupe_revenu"] == g and k in norm.get(c, {})]
            bias[k][g] = {"n": len(v), "moyenne": round(sum(v) / len(v), 1) if v else None}
    out["biais_revenu"] = bias

    # capacité fiscale (V-Dem) : diagnostic
    cap = {}
    vp = os.path.join(ROOT, "data/raw/vdem_extrait.csv")
    if os.path.exists(vp):
        fc = {}
        for r in csv.DictReader(open(vp, encoding="utf-8")):
            if r["year"] in ("2022", "2022.0", "2023", "2023.0") and r["v2stfisccap"] not in ("", "NA"):
                fc[r["country_text_id"]] = float(r["v2stfisccap"])
        for k in ("B5", "B6", "B3", "C2", "C3", "A1"):
            xs = [(data["obs"][c][k]["valeur_brute"], fc[c]) for c in fc if c in data["obs"] and k in data["obs"][c]]
            if len(xs) > 20:
                cap[k] = {"n": len(xs), "spearman_valeur_brute_vs_capacite_fiscale": round(S.spearman([a for a, _ in xs], [b for _, b in xs]), 3)}
        for k in ("B5", "B6", "C3", "C2"):
            xs = [(data["obs"][c][k]["valeur_brute"], data["obs"][c]["A4"]["valeur_brute"]) for c in data["obs"] if k in data["obs"][c] and "A4" in data["obs"][c]]
            cap.setdefault(k, {})["spearman_valeur_brute_vs_etat_de_droit_A4"] = round(S.spearman([a for a, _ in xs], [b for _, b in xs]), 3)
    out["capacite_fiscale"] = cap

    # corrélations
    ks = sorted(defs) + [a for a in ("B5n", "C4") if any(a in v for v in data["alt"].values())]
    allv = {c: dict(norm.get(c, {})) for c in pays}
    for a in ("B5n", "C4"):
        d2 = S.apply_overrides(data, {"ajouter": [a]})
        n2, _ = S.normalize(d2, "minmax", "obs", {a: next(i for i in d2["ind"]["indicateurs"] if i["id"] == a)})
        for c, v in n2.items():
            allv.setdefault(c, {}).update(v)
    corr = {}
    for a, b in itertools.combinations(ks, 2):
        cs = [c for c in allv if a in allv[c] and b in allv[c]]
        if len(cs) >= 20:
            corr[f"{a}~{b}"] = {"n": len(cs), "spearman": round(S.spearman([allv[c][a] for c in cs], [allv[c][b] for c in cs]), 3)}
    out["correlations"] = corr
    out["paires_fortes"] = {k: v for k, v in corr.items() if abs(v["spearman"]) >= 0.8}

    # compensation
    comp = {}
    for c in ranked:
        ds = [res[c]["dims"][d] for d in DIMS if res[c]["dims"][d] is not None]
        if len(ds) >= 2:
            comp[c] = round(max(ds) - min(ds), 1)
    out["compensation"] = {"n_ecart_sup_50": sum(1 for v in comp.values() if v > 50), "n_ecart_sup_70": sum(1 for v in comp.values() if v > 70),
                           "plus_forts": sorted(comp.items(), key=lambda t: -t[1])[:15]}

    # dominance d'un indicateur
    iw = {k: float(v.get("poids_interne", 1)) for k, v in defs.items()}
    rules = S.rules_of(d_eff)
    dom = {}
    for c in ranked:
        g0 = res[c]["global"]; best = (0.0, None, None)
        for k in res[c]["norm"]:
            if k not in defs:
                continue
            nv = {i: v for i, v in res[c]["norm"].items() if i != k}
            r = S.score_country(nv, ind_dim, W, None, rules["min_dimensions"], rules["exiger_dimension_A"], iw, rules["min_indicateurs"])
            if r["global"] is None:
                delta = None
            else:
                delta = r["global"] - g0
            if delta is None or abs(delta) > abs(best[0]):
                best = (delta if delta is not None else float("nan"), k, r["global"])
                if delta is None:
                    break
        dom[c] = {"indicateur": best[1], "delta": None if best[0] != best[0] else round(best[0], 2)}
    out["dominance"] = {"n_delta_sup_5": sum(1 for v in dom.values() if v["delta"] is not None and abs(v["delta"]) > 5),
                        "n_delta_sup_10": sum(1 for v in dom.values() if v["delta"] is not None and abs(v["delta"]) > 10),
                        "n_score_perdu_si_retrait": sum(1 for v in dom.values() if v["delta"] is None),
                        "par_pays": dom}
    dst = os.path.join(ROOT, "data/audit/diagnostic.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
    print("diagnostic →", dst)
    print(json.dumps({k: out[k] for k in ("couverture", "erreur_sous_ensembles", "capacite_fiscale", "paires_fortes", "compensation")}, ensure_ascii=False)[:6000])
    print({k: v for k, v in out["dominance"].items() if k != "par_pays"})


if __name__ == "__main__":
    main()
