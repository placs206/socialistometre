#!/usr/bin/env python3
"""Compare l'ancien indice composite V1.1 (archivé) aux coordonnées V2, uniquement pour documenter la rupture de méthode.
Les deux ne sont pas comparables ; aucune valeur V1 n'est utilisée par la V2.
Sortie : docs/comparaison_v1_v2.json
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.common import PROC, ROOT, write_json  # noqa: E402


def ranks(v):
    idx = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
            j += 1
        for k in range(i, j + 1):
            r[idx[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = ranks(x), ranks(y); n = len(x); mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num / den, 4)


def main():
    v1 = json.load(open(os.path.join(ROOT, "editions", "v1.1", "scores.json"), encoding="utf-8"))["pays"]
    co = json.load(open(os.path.join(PROC, "coordonnees.json"), encoding="utf-8"))
    pts = co["scenarios"][co["scenario_officiel"]]["points"]
    rows = []
    for iso, p in v1.items():
        if p.get("global") is None:
            continue
        q = pts.get(iso)
        rows.append({"iso3": iso, "nom": p["nom"], "v1_global": round(p["global"], 2), "v1_rang": p["rang"],
                     "v1_n_indicateurs": p["fiabilite"]["n_indicateurs"], "v1_dims": {k: round(v, 1) for k, v in p["dimensions"].items() if v is not None},
                     "x": q["x"]["v"] if q and q["x"] else None, "y": q["y"]["v"] if q and q["y"] else None})
    both = [r for r in rows if r["x"] is not None and r["y"] is not None]
    bx = [r for r in rows if r["x"] is not None]
    by = [r for r in rows if r["y"] is not None]
    peu = sorted([r for r in rows if r["v1_n_indicateurs"] <= 7], key=lambda r: r["v1_rang"])
    res = {
        "avertissement": "Comparaison descriptive : l'indice V1 (score composite 0-100, 4 dimensions pondérées 45/20/20/15) et les coordonnées V2 (scores officiels Fraser et V-Dem) ne mesurent pas la même chose.",
        "n_v1_avec_score": len(rows), "n_v1_et_v2_complet": len(both),
        "spearman_v1_global_vs_x_fraser": spearman([r["v1_global"] for r in bx], [r["x"] for r in bx]),
        "spearman_v1_global_vs_y_vdem": spearman([r["v1_global"] for r in by], [r["y"] for r in by]),
        "spearman_v1_dimA_vs_x_fraser": spearman([r["v1_dims"]["A"] for r in bx if "A" in r["v1_dims"]], [r["x"] for r in bx if "A" in r["v1_dims"]]),
        "spearman_v1_dimD_vs_y_vdem": spearman([r["v1_dims"]["D"] for r in by if "D" in r["v1_dims"]], [r["y"] for r in by if "D" in r["v1_dims"]]),
        "v1_scores_sur_7_indicateurs_ou_moins": [{k: r[k] for k in ("iso3", "nom", "v1_global", "v1_rang", "v1_n_indicateurs", "x", "y")} for r in peu],
        "v1_absents_de_fraser_et_vdem": [r["iso3"] for r in rows if r["x"] is None and r["y"] is None],
        "exemples": {r["iso3"]: {k: r[k] for k in ("v1_global", "v1_rang", "x", "y")} for r in rows if r["iso3"] in
                     ("CHL", "IRL", "CHE", "USA", "DNK", "SWE", "FRA", "SGP", "HKG", "CHN", "CUB", "VEN", "RUS", "MUS", "X-NCY", "X-NKR")},
    }
    write_json(os.path.join(ROOT, "docs", "comparaison_v1_v2.json"), res)
    print(json.dumps({k: v for k, v in res.items() if k.startswith("spearman") or k.startswith("n_")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
