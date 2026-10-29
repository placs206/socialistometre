#!/usr/bin/env python3
"""Recalcul indépendant des scores (audit) : réimplémentation pandas/numpy, sans importer engine/scoring.py.

Compare : (1) observations.csv + config → scores (méthode de base, sans décision approuvée) ; (2) data/processed/scores.json ;
(3) valeurs brutes embarquées dans dist/socialistometre.html. La parité des scores calculés dans le navigateur est testée par
tests/test_html.py. Si des décisions sont approuvées, ce recalcul indépendant ne s'applique qu'à la configuration de base.
Usage : python3 tools/audit/recalcul_independant.py   (code de sortie 1 si un écart > 1e-6 est trouvé)
"""
import json, os, re, sys
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
dim = J("config/dimensions.json"); cfgi = J("config/indicateurs.json")
W = {d["id"]: d["poids"] for d in dim["dimensions"]}
obs = pd.concat([pd.read_csv(os.path.join(ROOT, "data/processed", f), dtype={"iso3": str}) for f in ("observations.csv", "indicateurs_alt.csv")])
# Méthode officielle réimplémentée indépendamment : base + options retenues des décisions approuvées
RULES = {"min_indicateurs": {"A": 1, "B": 1, "C": 1, "D": 1}, "min_dimensions": 2, "exiger_dimension_A": True}
RULES.update(dim.get("regles_couverture", {}))
ind = [dict(i) for i in cfgi["indicateurs"]]
alts = {a["id"]: a for a in cfgi["alternatives_sensibilite"]}
for dcs in J("config/decisions.json")["decisions"]:
    if dcs.get("statut") != "approuvée":
        continue
    patch = next(o.get("patch") or {} for o in dcs["options"] if o["id"] == dcs["option_retenue"])
    for k, v in patch.get("regles", {}).items():
        if isinstance(v, dict): RULES[k] = {**RULES[k], **v}
        else: RULES[k] = v
    for a in patch.get("ajouter", []):
        if a not in [i["id"] for i in ind]: ind.append(dict(alts[a]))
    for k, ch in patch.get("indicateurs", {}).items():
        for i in ind:
            if i["id"] == k: i.update(ch)
ind = [i for i in ind if i.get("inclus", True)]
pays = pd.read_csv(os.path.join(ROOT, "data/processed/pays.csv"), dtype={"iso3": str}, keep_default_na=False)

rows = []
for d in ind:
    x = obs.loc[obs.indicateur == d["id"]].set_index("iso3")["valeur_brute"].astype(float)
    b = d["bornes"]
    if b["regle"] == "fixe":
        lo, hi = float(b["bas"]), float(b["haut"])
    else:
        lo, hi = np.percentile(x.values, [b["p_bas"], b["p_haut"]])  # interpolation linéaire (défaut numpy)
    t = ((x - lo) / (hi - lo)).clip(0, 1)
    s = 100 * t if d["orientation"] > 0 else 100 * (1 - t)
    rows.append(pd.DataFrame({"iso3": s.index, "ind": d["id"], "dim": d["dim"], "norm": s.values}))
N = pd.concat(rows)
N["w"] = N["ind"].map({i["id"]: float(i.get("poids_interne", 1)) for i in ind})
N["wn"] = N["w"] * N["norm"]
G = N.groupby(["iso3", "dim"])
moy = G["wn"].sum() / G["w"].sum()
nb = G["norm"].count()
seuil = [RULES["min_indicateurs"][d] for d in nb.index.get_level_values("dim")]
D = moy.where(nb.values >= seuil).unstack()     # dimension non calculée si trop peu d'indicateurs
D = D.reindex(pays.iso3).reindex(columns=list("ABCD"))
def glob(r):
    av = [k for k in "ABCD" if pd.notna(r[k])]
    if (RULES["exiger_dimension_A"] and pd.isna(r["A"])) or len(av) < RULES["min_dimensions"]:
        return np.nan
    return sum(W[k] * r[k] for k in av) / sum(W[k] for k in av)
D["G"] = D.apply(glob, axis=1)
D["rang"] = D["G"].round(9).rank(ascending=False, method="min")

sc = J("data/processed/scores.json")["pays"]
html = open(os.path.join(ROOT, "dist/socialistometre.html"), encoding="utf-8").read()
m = re.search(r"var DATA = (\{.*?\});\n", html, re.S)
hd = {p["id"]: p for p in json.loads(m.group(1).replace("<\\/", "</"))["pays"]}

ecarts, maxd = [], 0.0
approved = False   # les décisions approuvées sont réimplémentées ci-dessus
for iso, r in D.iterrows():
    s, h = sc[iso], hd[iso]
    if not approved:
        for k in "ABCD":
            a, b = r[k], s["dimensions"][k]
            if (pd.isna(a)) != (b is None):
                ecarts.append((iso, k, a, b)); continue
            if b is not None:
                dd = abs(a - b); maxd = max(maxd, dd)
                if dd > 1e-6: ecarts.append((iso, k, a, b))
        a, b = r["G"], s["global"]
        if (pd.isna(a)) != (b is None):
            ecarts.append((iso, "G", a, b))
        elif b is not None:
            dd = abs(a - b); maxd = max(maxd, dd)
            if dd > 1e-6 or int(r["rang"]) != s["rang"]:
                ecarts.append((iso, "G/rang", a, b, r["rang"], s["rang"]))
    for k, v in s["indicateurs"].items():
        o = obs[(obs.iso3 == iso) & (obs.indicateur == k)].drop_duplicates()
        if len(o) != 1 or abs(float(o.valeur_brute.iloc[0]) - v["brut"]) > 1e-9 or abs(h["raw"][k][0] - v["brut"]) > 1e-9:
            ecarts.append((iso, k, "brut"))
print(f"entités : {len(D)} ; scores globaux : {int(D.G.notna().sum())} ; écart max moteur/recalcul indépendant : {maxd:.2e} ; valeurs brutes moteur/HTML contrôlées ; écarts : {len(ecarts)}")
for e in ecarts[:30]: print("  ÉCART", e)
sys.exit(1 if ecarts else 0)
