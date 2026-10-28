#!/usr/bin/env python3
"""Batterie de tests de robustesse et de validation du Socialistomètre V1.

Produit : docs/robustesse.json (résultats complets), docs/ROBUSTESSE.md (lecture humaine), data/processed/stabilite.json
(intervalles de rang/score par pays, utilisés par l'interface). Graine fixe : exécution reproductible.
Code de sortie 1 si un test CRITIQUE échoue.
"""
import csv, hashlib, json, math, os, random, subprocess, sys, statistics

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402

DIMS = S.DIMS
SEED = 20261028
data = S.load()
defs = S.indicator_defs(data)
ind_dim = {k: v["dim"] for k, v in defs.items()}
W0 = S.dim_weights(data)
base, params, norm0 = S.compute(data)
ranked = [k for k, r in base.items() if r["global"] is not None]
g0 = {k: base[k]["global"] for k in ranked}
results, critiques = [], []


def record(tid, nom, statut, detail, critique=False, mesures=None):
    results.append({"id": tid, "nom": nom, "statut": statut, "critique": critique, "detail": detail, "mesures": mesures or {}})
    if critique and statut != "RÉUSSI":
        critiques.append(tid)
    print(f"[{statut}] {tid} {nom} — {detail}")


def gscore(dims, w, require_a=True, min_dims=2):
    avail = [d for d in DIMS if dims[d] is not None and w.get(d, 0) > 0]
    if len(avail) < min_dims or (require_a and dims["A"] is None):
        return None
    ws = sum(w[d] for d in avail)
    return sum(w[d] * dims[d] for d in avail) / ws


def comparer(g_alt, label=""):
    common = [k for k in ranked if g_alt.get(k) is not None]
    rho = S.spearman([g0[k] for k in common], [g_alt[k] for k in common])
    r0 = S.competition_rank({k: g0[k] for k in common}); r1 = S.competition_rank({k: g_alt[k] for k in common})
    shifts = sorted(abs(r0[k] - r1[k]) for k in common)
    dif = [abs(g0[k] - g_alt[k]) for k in common]
    return {"n": len(common), "spearman": rho, "decalage_rang_median": statistics.median(shifts), "decalage_rang_max": shifts[-1],
            "ecart_score_moyen": sum(dif) / len(dif), "ecart_score_max": max(dif)}


# ------------------------------------------------------------------ T01 vérification mathématique indépendante (numpy)
def t01():
    import numpy as np
    obs = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "data/processed/observations.csv"), encoding="utf-8")):
        obs.setdefault(r["indicateur"], {})[r["iso3"]] = float(r["valeur_brute"])
    cfg = json.load(open(os.path.join(ROOT, "config/indicateurs.json"), encoding="utf-8"))["indicateurs"]
    normi = {}
    for i in cfg:
        v = np.array(list(obs[i["id"]].values()))
        if i["bornes"]["regle"] == "fixe":
            lo, hi = i["bornes"]["bas"], i["bornes"]["haut"]
        else:
            lo, hi = np.percentile(v, i["bornes"]["p_bas"]), np.percentile(v, i["bornes"]["p_haut"])
        for c, x in obs[i["id"]].items():
            t = min(1.0, max(0.0, (x - lo) / (hi - lo)))
            normi.setdefault(c, {})[i["id"]] = 100 * t if i["orientation"] > 0 else 100 * (1 - t)
    w = {"A": 0.45, "B": 0.20, "C": 0.20, "D": 0.15}
    sc = json.load(open(os.path.join(ROOT, "data/processed/scores.json"), encoding="utf-8"))["pays"]
    maxdiff, n = 0.0, 0
    for c, nv in normi.items():
        dims = {}
        for d in DIMS:
            xs = [nv[i["id"]] for i in cfg if i["dim"] == d and i["id"] in nv]
            dims[d] = float(np.mean(xs)) if xs else None
        avail = [d for d in DIMS if dims[d] is not None]
        g = None
        if len(avail) >= 2 and dims["A"] is not None:
            g = sum(w[d] * dims[d] for d in avail) / sum(w[d] for d in avail)
        s = sc[c]
        for d in DIMS:
            a, b = dims[d], s["dimensions"][d]
            assert (a is None) == (b is None), (c, d)
            if a is not None:
                maxdiff = max(maxdiff, abs(a - b)); n += 1
        assert (g is None) == (s["global"] is None), c
        if g is not None:
            maxdiff = max(maxdiff, abs(g - s["global"])); n += 1
        for k, v in nv.items():
            maxdiff = max(maxdiff, abs(v - s["indicateurs"][k]["norm"])); n += 1
    ok = maxdiff < 1e-4  # scores.json est arrondi à 6 décimales
    record("T01", "Recalcul mathématique indépendant (numpy) de toutes les valeurs normalisées, dimensions et scores globaux",
           "RÉUSSI" if ok else "ÉCHEC", f"{n} valeurs comparées ; écart maximal {maxdiff:.2e} (arrondi du fichier : 1e-6)", True, {"ecart_max": maxdiff, "valeurs": n})


# ------------------------------------------------------------------ T02 doublons et incohérences
def t02():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data/processed/observations.csv"), encoding="utf-8")))
    pays = list(csv.DictReader(open(os.path.join(ROOT, "data/processed/pays.csv"), encoding="utf-8")))
    keys = [(r["iso3"], r["indicateur"]) for r in rows]
    dup = len(keys) - len(set(keys))
    ids = [p["iso3"] for p in pays]
    dup_ids = len(ids) - len(set(ids))
    orphelins = [r["iso3"] for r in rows if r["iso3"] not in set(ids)]
    noms_dup = [n for n, c in __import__("collections").Counter(p["nom_fr"] for p in pays).items() if c > 1]
    anom = list(csv.DictReader(open(os.path.join(ROOT, "data/processed/anomalies.csv"), encoding="utf-8")))
    erreurs = [a for a in anom if a["niveau"] == "erreur"]
    fenetre = [r for r in rows if not (2019 <= int(r["annee"]) <= 2023)]
    vide = [r for r in rows if not r["url_source"] or not r["source"]]
    ok = not (dup or dup_ids or orphelins or erreurs or fenetre or vide or noms_dup)
    record("T02", "Détection des doublons et incohérences (clés, identifiants, noms, années, traçabilité, erreurs du journal)",
           "RÉUSSI" if ok else "ÉCHEC",
           f"doublons observations={dup}, doublons identifiants={dup_ids}, observations orphelines={len(orphelins)}, noms en double={noms_dup}, "
           f"erreurs de journal={len(erreurs)}, hors fenêtre={len(fenetre)}, sans source/URL={len(vide)}", True,
           {"doublons": dup, "orphelins": len(orphelins), "erreurs_journal": len(erreurs)})


# ------------------------------------------------------------------ T03 données brutes : empreintes et contrôle d'échantillon
def t03():
    man = json.load(open(os.path.join(ROOT, "data/raw/MANIFEST.json"), encoding="utf-8"))["fichiers"]
    bad = [n for n, m in man.items() if hashlib.sha256(open(os.path.join(ROOT, "data/raw", n), "rb").read()).hexdigest() != m["sha256"]]
    rnd = random.Random(SEED)
    rows = list(csv.DictReader(open(os.path.join(ROOT, "data/processed/observations.csv"), encoding="utf-8")))
    echant = rnd.sample(rows, 120)
    # contrôle croisé : relecture indépendante des fichiers bruts pour WB et OCDE CIT/PIT/Kaitz, FH
    wbcode = {"A1": "TM.TAX.MRCH.SM.AR.ZS", "B1": "GC.REV.SOCL.ZS", "C2": "SE.PRM.PRIV.ZS", "C3": "NE.CON.GOVT.ZS",
              "A4": "GOV_WGI_RL.EST", "A5": "GOV_WGI_RQ.EST", "D1": "GOV_WGI_VA.EST"}
    cache, echec, verifie = {}, [], 0
    import openpyxl
    fh = None
    for r in echant:
        ind, iso3, val, an = r["indicateur"], r["iso3"], float(r["valeur_brute"]), int(r["annee"])
        ref = None
        if ind in wbcode:
            if ind not in cache:
                cache[ind] = {}
                for pg in json.load(open(os.path.join(ROOT, f"data/raw/wb_{wbcode[ind]}.json"), encoding="utf-8")):
                    for x in pg[1] or []:
                        if x["value"] is not None:
                            cache[ind][(x["countryiso3code"], int(x["date"]))] = float(x["value"])
            ref = cache[ind].get((iso3, an))
        elif ind in ("B3", "B2", "B4"):
            f = {"B3": "oecd_cit.csv", "B2": "oecd_pit_top.csv", "B4": "oecd_min2ave.csv"}[ind]
            for x in csv.DictReader(open(os.path.join(ROOT, "data/raw", f), encoding="utf-8")):
                if x["REF_AREA"] == iso3 and int(x["TIME_PERIOD"]) == an and x["OBS_VALUE"] != "":
                    if (ind == "B3" and x["MEASURE"] == "CIT_C" and x["TARGETING"] == "ST" and x["SECTOR"] == "S13") or \
                       (ind == "B2" and x["MEASURE"] == "TS_PIT") or (ind == "B4" and x["AGGREGATION_OPERATION"] == "MEDIAN"):
                        ref = float(x["OBS_VALUE"]) / (100.0 if ind == "B4" else 1.0)
        elif ind in ("A2", "A3", "C1"):
            vals = {}
            for f in ("oecd_pmr.csv", "oecd_pmr_wbg.csv"):
                for x in csv.DictReader(open(os.path.join(ROOT, "data/raw", f), encoding="utf-8")):
                    if x["REF_AREA"] == iso3 and x["TIME_PERIOD"] == "2023" and x["OBS_VALUE"] != "":
                        vals.setdefault(x["MEASURE"], float(x["OBS_VALUE"]))
            if ind == "A2":
                ref = sum(vals[m] for m in ["LAWYERS", "ACCOUNTANTS", "ARCHITECTS", "ENGINEERS", "ESTATEAGENTS"]) / 5
            else:
                ref = vals.get({"A3": "PRICE", "C1": "PUBLIC_OWNER"}[ind])
        else:  # Freedom House
            if fh is None:
                ws = openpyxl.load_workbook(os.path.join(ROOT, "data/raw/freedomhouse_fiw_2013-2024.xlsx"), read_only=True, data_only=True)["FIW13-24"]
                rr = list(ws.iter_rows(values_only=True)); h = rr[1]
                fh = {x[0]: dict(zip(h, x)) for x in rr[2:] if x[0] and x[3] == 2024}
            p = {q["iso3"]: q for q in csv.DictReader(open(os.path.join(ROOT, "data/processed/pays.csv"), encoding="utf-8"))}[iso3]
            row = fh.get(p["nom_en"]) or next((v for n, v in fh.items() if n.startswith(p["nom_en"].split(",")[0])), None)
            col = {"A6": "G2", "D2": "PR", "D3": "D", "D4": "E"}[ind]
            ref = float(row[col]) if row else None
        verifie += 1
        if ref is None or abs(ref - val) > 1e-4:
            echec.append((iso3, ind, val, ref))
    ok = not bad and len(echec) <= 3  # le rapprochement FH par nom peut échouer sur quelques noms ; seuil documenté
    detail = f"{len(man)} fichiers bruts : {len(bad)} empreinte(s) divergente(s) ; échantillon de {verifie} observations relu dans les fichiers bruts : {len(echec)} écart(s)"
    if echec:
        detail += " " + str(echec[:5])
    record("T03", "Données brutes : empreintes SHA-256 du manifeste et relecture indépendante d'un échantillon (120 obs.)",
           "RÉUSSI" if ok else "ÉCHEC", detail, True, {"fichiers": len(man), "divergences": len(bad), "echantillon": verifie, "ecarts": len(echec)})


# ------------------------------------------------------------------ T04 valeurs normalisées
def t04():
    probs = []
    cor = {}
    for k, d in defs.items():
        xs = [(data["obs"][c][k]["valeur_brute"], norm0[c][k]) for c in norm0 if k in norm0[c]]
        if any(not (-1e-9 <= n <= 100 + 1e-9) for _, n in xs):
            probs.append((k, "hors [0,100]"))
        rho = S.spearman([x for x, _ in xs], [n for _, n in xs])
        cor[k] = rho
        if rho * d["orientation"] < 0.95:
            probs.append((k, f"orientation/monotonie douteuse (rho={rho:.3f})"))
    ext = {k: (min(v["valeur_brute"] for c in data["obs"].values() for kk, v in c.items() if kk == k),
               max(v["valeur_brute"] for c in data["obs"].values() for kk, v in c.items() if kk == k)) for k in defs}
    record("T04", "Données brutes et normalisées : plage [0,100], monotonie et sens d'orientation de chaque indicateur",
           "RÉUSSI" if not probs else "ÉCHEC", f"{len(defs)} indicateurs contrôlés ; problèmes : {probs or 'aucun'}", True,
           {"spearman_brut_norm_x_orientation": {k: round(cor[k] * defs[k]['orientation'], 4) for k in cor}})


# ------------------------------------------------------------------ T05 sensibilité aux pondérations
def t05():
    scen = {}
    for d in DIMS:
        for delta in (-0.10, 0.10):
            w = dict(W0); w[d] = max(0.0, W0[d] + delta)
            rest = 1 - w[d]; others = [x for x in DIMS if x != d]; so = sum(W0[x] for x in others)
            for x in others:
                w[x] = W0[x] * rest / so
            scen[f"{d} {delta:+.0%}"] = w
    scen["poids égaux 25 %"] = {d: 0.25 for d in DIMS}
    out = {}
    for name, w in scen.items():
        g = {k: gscore(base[k]["dims"], w) for k in ranked}
        out[name] = comparer(g)
    rnd = random.Random(SEED)
    rhos, maxshift, cnt = [], [], {k: [] for k in ranked}
    for _ in range(2000):
        gam = [rnd.gammavariate(W0[d] * 40, 1) for d in DIMS]; t = sum(gam)
        w = {d: gam[i] / t for i, d in enumerate(DIMS)}
        g = {k: gscore(base[k]["dims"], w) for k in ranked}
        c = comparer(g); rhos.append(c["spearman"]); maxshift.append(c["decalage_rang_median"])
    mc = {"tirages": 2000, "loi": "Dirichlet(40·w)", "spearman_min": min(rhos), "spearman_moyen": sum(rhos) / len(rhos),
          "spearman_p5": sorted(rhos)[100], "decalage_rang_median_moyen": sum(maxshift) / len(maxshift)}
    pire = min(v["spearman"] for v in out.values())
    statut = "RÉUSSI" if pire >= 0.95 and mc["spearman_p5"] >= 0.98 else "AVERTISSEMENT"
    record("T05", "Analyse de sensibilité aux pondérations (±10 points par dimension, poids égaux, 2 000 tirages Dirichlet)", statut,
           f"Spearman minimal sur scénarios déterministes : {pire:.4f} ; Monte-Carlo : moyenne {mc['spearman_moyen']:.4f}, P5 {mc['spearman_p5']:.4f}, min {mc['spearman_min']:.4f}",
           False, {"scenarios": out, "monte_carlo": mc})


# ------------------------------------------------------------------ T06 retrait d'un indicateur à la fois
def t06():
    out = {}
    for k in defs:
        inc = set(defs) - {k}
        g = {}
        for c in ranked:
            r = S.score_country(norm0[c], ind_dim, W0, inc)
            g[c] = r["global"]
        cmp = comparer(g)
        pires = sorted(((abs(g0[c] - g[c]), c) for c in ranked if g[c] is not None), reverse=True)[:3]
        cmp["pays_les_plus_affectes"] = [(data["pays"][c]["nom_fr"], round(d, 2)) for d, c in pires]
        cmp["n_sans_score"] = sum(1 for c in ranked if g[c] is None)
        out[k] = cmp
    pire = min(v["spearman"] for v in out.values()); kk = min(out, key=lambda x: out[x]["spearman"])
    record("T06", "Recalcul en retirant un indicateur à la fois (17 recalculs)", "RÉUSSI" if pire >= 0.97 else "AVERTISSEMENT",
           f"Spearman minimal {pire:.4f} (retrait de {kk}) ; écart de score moyen max {max(v['ecart_score_moyen'] for v in out.values()):.2f} pts", False, out)


# ------------------------------------------------------------------ T07 méthodes de normalisation
def t07():
    out = {}
    variants = {}
    for m in ("rang", "zscore"):
        res, _, _ = S.compute(data, m)
        variants[m] = {k: r["global"] for k, r in res.items() if r["global"] is not None}
    # bornes tout en percentiles P5-P95 (même sur les échelles naturelles)
    import copy
    d2 = copy.deepcopy(data)
    for i in d2["ind"]["indicateurs"]:
        i["bornes"] = {"regle": "percentile", "p_bas": 5, "p_haut": 95}
    res, _, _ = S.compute(d2, "minmax"); variants["minmax_percentiles_partout"] = {k: r["global"] for k, r in res.items() if r["global"] is not None}
    d3 = copy.deepcopy(data)
    for i in d3["ind"]["indicateurs"]:
        if i["bornes"]["regle"] == "percentile":
            i["bornes"] = {"regle": "percentile", "p_bas": 10, "p_haut": 90}
    res, _, _ = S.compute(d3, "minmax"); variants["minmax_P10_P90"] = {k: r["global"] for k, r in res.items() if r["global"] is not None}
    for m, g in variants.items():
        out[m] = comparer(g)
    pire = min(v["spearman"] for v in out.values())
    record("T07", "Comparaison de plusieurs méthodes de normalisation (rang, z-score logistique, percentiles partout, P10-P90)",
           "RÉUSSI" if pire >= 0.93 else "AVERTISSEMENT", f"Spearman minimal par rapport à la méthode principale : {pire:.4f}", False, out)


# ------------------------------------------------------------------ T08 stabilité des rangs (rééchantillonnage d'indicateurs + poids)
def t08():
    rnd = random.Random(SEED + 1)
    inds = list(defs); n = 600
    ranks = {c: [] for c in ranked}; scs = {c: [] for c in ranked}
    for _ in range(n):
        inc = {k for k in inds if rnd.random() < 0.8}
        gam = [rnd.gammavariate(W0[d] * 40, 1) for d in DIMS]; t = sum(gam)
        w = {d: gam[i] / t for i, d in enumerate(DIMS)}
        g = {}
        for c in ranked:
            g[c] = S.score_country(norm0[c], ind_dim, w, inc)["global"]
        rk = S.competition_rank({c: v for c, v in g.items() if v is not None})
        for c in ranked:
            if g[c] is not None:
                ranks[c].append(rk[c]); scs[c].append(g[c])
    def q(v, p):
        v = sorted(v); return v[min(len(v) - 1, int(p / 100 * len(v)))]
    inter = {}
    for c in ranked:
        if len(ranks[c]) > 30:
            inter[c] = {"rang_p5": q(ranks[c], 5), "rang_p95": q(ranks[c], 95), "score_p5": round(q(scs[c], 5), 3), "score_p95": round(q(scs[c], 95), 3),
                        "n_tirages": len(ranks[c])}
    largeur = sorted(v["rang_p95"] - v["rang_p5"] for v in inter.values())
    json.dump({"graine": SEED + 1, "tirages": n, "methode": "80 % des indicateurs retenus au hasard + poids Dirichlet(40·w)", "intervalles": inter},
              open(os.path.join(ROOT, "data/processed/stabilite.json"), "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, indent=1)
    record("T08", "Stabilité des rangs et des scores (600 rééchantillonnages : 80 % des indicateurs + poids perturbés)", "RÉUSSI",
           f"largeur médiane de l'intervalle de rang P5-P95 : {statistics.median(largeur)} places ; P90 : {largeur[int(0.9*len(largeur))]} places ; "
           f"intervalles enregistrés pour {len(inter)} entités (affichés dans l'interface)", False,
           {"largeur_mediane": statistics.median(largeur), "largeur_p90": largeur[int(0.9 * len(largeur))], "n_entites": len(inter)})


# ------------------------------------------------------------------ T09 comportement en présence de données manquantes
def t09():
    comp = [c for c in ranked if S.statut_couverture(base[c]) == "complet"]
    rnd = random.Random(SEED + 2)
    errs, rhos = [], []
    for _ in range(300):
        g = {}
        for c in comp:
            nv = {k: v for k, v in norm0[c].items() if rnd.random() > 0.33}
            g[c] = S.score_country(nv, ind_dim, W0)["global"]
        got = [c for c in comp if g[c] is not None]
        errs += [abs(g[c] - g0[c]) for c in got]
        rhos.append(S.spearman([g0[c] for c in got], [g[c] for c in got]))
    errs.sort()
    # règle « A obligatoire » : comparaison avec la règle assouplie (au moins 2 dimensions, A non exigée)
    res2, _, _ = S.compute(data, "minmax", None, None, 2, False)
    g2 = {k: r["global"] for k, r in res2.items() if r["global"] is not None}
    nouveaux = [data["pays"][k]["nom_fr"] for k in g2 if k not in g0]
    cmp = comparer({k: v for k, v in g2.items()})
    # cohérence des avertissements
    sc = json.load(open(os.path.join(ROOT, "data/processed/scores.json"), encoding="utf-8"))["pays"]
    incoh = [k for k, p in sc.items() if p["statut_couverture"] in ("partiel", "insuffisant") and not p["avertissements"]]
    incoh += [k for k, p in sc.items() if p["global"] is not None and p["dimensions"]["A"] is None]
    sans = [k for k, p in sc.items() if p["statut_couverture"] == "aucune donnée" and p["global"] is not None]
    ok = not incoh and not sans
    record("T09", "Comportement en présence de données manquantes (masquage aléatoire de 1/3 des indicateurs ; règle « dimension A exigée » ; avertissements)",
           "RÉUSSI" if ok else "ÉCHEC",
           f"masquage 1/3 sur {len(comp)} pays complets × 300 tirages : écart absolu médian {errs[len(errs)//2]:.2f} pts, P95 {errs[int(.95*len(errs))]:.2f} pts, "
           f"Spearman moyen {sum(rhos)/len(rhos):.4f} ; règle assouplie (A non exigée) ajouterait {len(nouveaux)} entités à score global ({', '.join(nouveaux[:6])}…) ; "
           f"incohérences d'avertissements : {len(incoh) + len(sans)}", True,
           {"ecart_median": errs[len(errs) // 2], "ecart_p95": errs[int(.95 * len(errs))], "spearman_moyen": sum(rhos) / len(rhos),
            "regle_assouplie_nouveaux": nouveaux, "regle_assouplie_spearman": cmp["spearman"]})


# ------------------------------------------------------------------ T10 variantes d'indicateurs et redondances
def t10():
    alt = data["alt"]
    out = {}
    for rid, aid in (("A1", "A1alt"), ("C2", "C2alt")):
        d2 = {"obs": {c: ({**data["obs"][c], aid: alt[c][aid]} if c in alt and aid in alt[c] else dict(data["obs"][c])) for c in data["obs"]}}
        for c in d2["obs"]:
            if c in alt and aid in alt[c]:
                pass
        # remplacement : on substitue l'indicateur par sa variante là où la variante existe (sinon absent)
        data2 = dict(data); data2["obs"] = {}
        for c, d in data["obs"].items():
            nd = {k: v for k, v in d.items() if k != rid}
            if c in alt and aid in alt[c]:
                nd[rid] = alt[c][aid]
            data2["obs"][c] = nd
        res, _, _ = S.compute(data2)
        out[f"{rid}→{aid}"] = comparer({k: r["global"] for k, r in res.items() if r["global"] is not None})
    # redondance entre indicateurs d'une même dimension
    red = {}
    for d in DIMS:
        ks = [k for k in defs if ind_dim[k] == d]
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                common = [c for c in norm0 if ks[i] in norm0[c] and ks[j] in norm0[c]]
                if len(common) >= 15:
                    red[f"{ks[i]}~{ks[j]}"] = {"n": len(common), "spearman": round(S.spearman([norm0[c][ks[i]] for c in common], [norm0[c][ks[j]] for c in common]), 3)}
    fortes = {k: v for k, v in red.items() if abs(v["spearman"]) >= 0.85}
    record("T10", "Variantes d'indicateurs (tarif pondéré ; scolarisation privée secondaire) et redondances intra-dimension", "RÉUSSI",
           f"variantes : " + ", ".join(f"{k} ρ={v['spearman']:.4f}" for k, v in out.items()) + f" ; paires redondantes (|ρ|≥0,85) : {fortes or 'aucune'}",
           False, {"variantes": out, "correlations_intra_dimension": red})


# ------------------------------------------------------------------ T11 corrélations inter-dimensions (relation liberté économique / politique)
def t11():
    comp = [c for c in ranked if S.statut_couverture(base[c]) == "complet"]
    m = {}
    for i, a in enumerate(DIMS):
        for b in DIMS[i + 1:]:
            m[f"{a}-{b}"] = round(S.spearman([base[c]["dims"][a] for c in comp], [base[c]["dims"][b] for c in comp]), 3)
    record("T11", "Corrélations de rang entre dimensions (pays à score complet) — documentation de la relation liberté économique / liberté politique (Friedman, p. 51)",
           "INFORMATIF", f"n={len(comp)} ; " + ", ".join(f"{k}: {v}" for k, v in m.items()) + " (corrélation ≠ causalité)", False, m)


# ------------------------------------------------------------------ T12 reproductibilité
def t12():
    files = ["data/processed/pays.csv", "data/processed/observations.csv", "data/processed/indicateurs_alt.csv", "data/processed/anomalies.csv", "data/processed/scores.json"]
    h = lambda: {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest() for f in files}
    avant = h()
    for cmd in (["tools/build_dataset.py"], ["engine/scoring.py"]):
        subprocess.run([sys.executable, os.path.join(ROOT, *cmd[0].split("/"))], check=True, capture_output=True)
    apres = h()
    diff = [f for f in files if avant[f] != apres[f]]
    record("T12", "Reproductibilité d'une édition : reconstruction complète depuis data/raw (jeu de données + scores) et comparaison d'empreintes",
           "RÉUSSI" if not diff else "ÉCHEC", f"{len(files)} fichiers recalculés ; divergences : {diff or 'aucune'} ; empreinte du jeu de données {S.dataset_hash()[:16]}…", True,
           {"empreintes": apres, "empreinte_jeu_de_donnees": S.dataset_hash()})


def main():
    for f in (t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12):
        try:
            f()
        except Exception as e:  # noqa
            import traceback
            record(f.__name__.upper(), f.__name__, "ÉCHEC", f"exception : {e!r} {traceback.format_exc()[-300:]}", True)
    out = {"version_methodologie": data["dim"]["version_methodologie"], "graine": SEED, "tests": results, "echecs_critiques": critiques}
    json.dump(out, open(os.path.join(ROOT, "docs", "robustesse.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    lines = ["# Tests de robustesse et de validation — Socialistomètre V1.0", "",
             "Généré par `python3 tools/run_robustness.py` (graine %d). Les tests marqués CRITIQUE bloquent la validation en cas d'échec." % SEED, "",
             "| Test | Nom | Critique | Résultat | Détail |", "|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['id']} | {r['nom']} | {'oui' if r['critique'] else 'non'} | **{r['statut']}** | {r['detail'].replace('|', '/')} |")
    lines += ["", f"Échecs critiques : {critiques or 'aucun'}"]
    open(os.path.join(ROOT, "docs", "ROBUSTESSE.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    sys.exit(1 if critiques else 0)


if __name__ == "__main__":
    main()
