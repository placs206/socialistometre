#!/usr/bin/env python3
"""Moteur de normalisation et de calcul du Socialistomètre (méthodologie : voir config/dimensions.json).

Lecture seule de data/processed/ et config/ ; écrit data/processed/scores.json (déterministe : aucune date, aucun aléa).

Conventions
-----------
* Tous les indicateurs sont orientés sur 0 (pôle socialisant) → 100 (pôle libéral) selon `orientation` (+1 : valeur brute haute = libéral ;
  -1 : valeur brute haute = socialisant).
* Normalisation principale « minmax » : transformation linéaire bornée [0,100] avec bornes fixes (échelles naturelles) ou percentiles P5-P95 de la
  distribution mondiale de l'indicateur (valeurs hors bornes ramenées aux bornes).
* Score de dimension = moyenne simple des indicateurs disponibles de la dimension (poids égaux).
* Score global = Σ w_d·S_d / Σ w_d sur les dimensions disponibles. Il n'est calculé que si la dimension A (poids 45 %) est disponible
  ET si au moins 2 dimensions sont disponibles ; sinon les scores de dimension restent affichés, sans score global ni rang.

Paramétrage (audit 2026-10-28) — tout est piloté par la configuration, aucune règle n'est codée en dur pour un pays :
* `config/dimensions.json` → `regles_couverture` : nombre minimal d'indicateurs pour qu'une dimension soit calculée,
  nombre minimal de dimensions et exigence de la dimension A pour le score global (valeurs par défaut = règle V1.1).
* `config/indicateurs.json` → par indicateur : `inclus` (défaut true), `poids_interne` (défaut 1), `bornes`, `orientation`.
* `config/decisions.json` → registre des décisions ; chaque décision porte un `patch` (surcharges ci-dessus).
  Méthode officielle = configuration de base + patchs des décisions au statut « approuvée ».
  Les autres décisions ne servent qu'aux scénarios (jamais au score de référence).
* Score de dimension = moyenne pondérée (poids internes) des indicateurs inclus disponibles.
* Contribution d'un indicateur au score global = (w_d / Σ w_d disponibles) × (w_i / Σ w_i disponibles dans d) × score_i ;
  la somme des contributions est égale au score global (vérifié par les tests).
"""
import copy, csv, hashlib, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
CFG = os.path.join(ROOT, "config")
DIMS = ["A", "B", "C", "D"]


# ----------------------------------------------------------------------------- chargement
def _csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load(proc=None):
    """proc : répertoire des données traitées (défaut data/processed ; autre valeur : test de période T14)."""
    PROC_ = proc or PROC
    cfg_dim = json.load(open(os.path.join(CFG, "dimensions.json"), encoding="utf-8"))
    cfg_ind = json.load(open(os.path.join(CFG, "indicateurs.json"), encoding="utf-8"))
    pays = {p["iso3"]: p for p in _csv(os.path.join(PROC_, "pays.csv"))}
    obs, alt = {}, {}
    for r in _csv(os.path.join(PROC_, "observations.csv")):
        r["valeur_brute"] = float(r["valeur_brute"]); r["annee"] = int(r["annee"])
        obs.setdefault(r["iso3"], {})[r["indicateur"]] = r
    for r in _csv(os.path.join(PROC_, "indicateurs_alt.csv")):
        r["valeur_brute"] = float(r["valeur_brute"]); r["annee"] = int(r["annee"])
        alt.setdefault(r["iso3"], {})[r["indicateur"]] = r
    dec_path = os.path.join(CFG, "decisions.json")
    cfg_dec = json.load(open(dec_path, encoding="utf-8")) if os.path.exists(dec_path) else {"decisions": []}
    return {"dim": cfg_dim, "ind": cfg_ind, "pays": pays, "obs": obs, "alt": alt, "decisions": cfg_dec}


def dataset_hash():
    """Empreinte SHA-256 du jeu de données et de la configuration de l'édition."""
    h = hashlib.sha256()
    for rel in ("data/processed/pays.csv", "data/processed/observations.csv", "data/processed/indicateurs_alt.csv",
                "data/raw/MANIFEST.json", "config/dimensions.json", "config/indicateurs.json", "config/decisions.json"):
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        h.update(rel.encode())
        h.update(hashlib.sha256(open(os.path.join(ROOT, rel), "rb").read()).digest())
    return h.hexdigest()


# ----------------------------------------------------------------------------- statistiques
def percentile(sorted_vals, p):
    """Percentile par interpolation linéaire (identique à numpy.percentile par défaut)."""
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (n - 1) * p / 100.0
    lo = int(math.floor(k)); hi = min(lo + 1, n - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def spearman(x, y):
    def ranks(v):
        idx = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
        while i < len(idx):
            j = i
            while j + 1 < len(idx) and v[idx[j + 1]] == v[idx[i]]:
                j += 1
            for k in range(i, j + 1):
                r[idx[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y); n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


# ----------------------------------------------------------------------------- normalisation
def indicator_defs(data, with_alt=False):
    """Indicateurs retenus dans le calcul (les indicateurs `inclus: false` sont écartés)."""
    defs = {i["id"]: i for i in data["ind"]["indicateurs"] if i.get("inclus", True)}
    if with_alt:
        for a in data["ind"]["alternatives_sensibilite"]:
            defs[a["id"]] = a
    return defs


def bounds_for(defn, values):
    b = defn["bornes"]
    if b["regle"] == "fixe":
        return float(b["bas"]), float(b["haut"])
    sv = sorted(values)
    return percentile(sv, b["p_bas"]), percentile(sv, b["p_haut"])


def normalize(data, method="minmax", source="obs", defs=None):
    """Retourne (norm, params) : norm[iso3][ind] ∈ [0,100] ; params[ind] décrit la transformation."""
    obs = data[source]
    defs = defs or indicator_defs(data)
    by_ind = {}
    for iso3, d in obs.items():
        for k, r in d.items():
            by_ind.setdefault(k, []).append(r["valeur_brute"])
    params, norm = {}, {}
    for k, vals in by_ind.items():
        if k not in defs:
            continue
        o = defs[k]["orientation"]
        sv = sorted(vals)
        if method == "minmax":
            lo, hi = bounds_for(defs[k], vals)
            params[k] = {"methode": "minmax", "bas": lo, "haut": hi, "orientation": o}
            f = lambda x, lo=lo, hi=hi, o=o: (lambda t: (100 * t if o > 0 else 100 * (1 - t)))(min(1.0, max(0.0, (x - lo) / (hi - lo))))
        elif method == "rang":
            n = len(sv)
            params[k] = {"methode": "rang", "n": n, "orientation": o}
            import bisect
            def f(x, sv=sv, n=n, o=o):
                less = bisect.bisect_left(sv, x); leq = bisect.bisect_right(sv, x)
                r = 100.0 * (less + 0.5 * (leq - less)) / n
                return r if o > 0 else 100.0 - r
        elif method == "zscore":
            lo, hi = percentile(sv, 1), percentile(sv, 99)
            w = [min(hi, max(lo, v)) for v in vals]
            mu = sum(w) / len(w); sd = math.sqrt(sum((v - mu) ** 2 for v in w) / (len(w) - 1))
            params[k] = {"methode": "zscore", "moyenne": mu, "ecart_type": sd, "winsor": [lo, hi], "orientation": o}
            def f(x, mu=mu, sd=sd, lo=lo, hi=hi, o=o):
                z = (min(hi, max(lo, x)) - mu) / sd
                return 100.0 * phi(z if o > 0 else -z)
        else:
            raise ValueError(method)
        for iso3, d in obs.items():
            if k in d:
                norm.setdefault(iso3, {})[k] = f(d[k]["valeur_brute"])
    return norm, params


# ----------------------------------------------------------------------------- scores
def dim_weights(data):
    return {d["id"]: d["poids"] for d in data["dim"]["dimensions"]}


DEFAULT_RULES = {"min_indicateurs": {"A": 1, "B": 1, "C": 1, "D": 1}, "min_dimensions": 2, "exiger_dimension_A": True}


def rules_of(data):
    r = copy.deepcopy(DEFAULT_RULES)
    r.update(copy.deepcopy(data["dim"].get("regles_couverture", {})))
    return r


def score_country(nv, ind_dim, weights, included=None, min_dims=2, require_a=True, iw=None, min_ind=None):
    """nv : {ind: valeur normalisée} ; ind_dim : {ind: dim} ; iw : poids internes {ind: w} (défaut 1) ;
    min_ind : {dim: nombre minimal d'indicateurs disponibles pour calculer la dimension} (défaut 1).
    Retourne dimensions, global, dimensions disponibles, contributions de chaque indicateur au score global."""
    iw = iw or {}; min_ind = min_ind or {}
    sums, wts, cnt = {d: 0.0 for d in DIMS}, {d: 0.0 for d in DIMS}, {d: 0 for d in DIMS}
    used = {d: [] for d in DIMS}
    for k, v in nv.items():
        if k not in ind_dim or (included is not None and k not in included):
            continue
        w = float(iw.get(k, 1.0))
        if w <= 0:
            continue
        d = ind_dim[k]
        sums[d] += w * v; wts[d] += w; cnt[d] += 1; used[d].append(k)
    dims = {d: (sums[d] / wts[d] if cnt[d] and cnt[d] >= min_ind.get(d, 1) else None) for d in DIMS}
    insuff = [d for d in DIMS if cnt[d] and dims[d] is None]
    avail = [d for d in DIMS if dims[d] is not None and weights.get(d, 0) > 0]
    g = None; contrib = {}
    if len(avail) >= min_dims and (not require_a or dims["A"] is not None):
        wsum = sum(weights[d] for d in avail)
        if wsum > 0:
            g = sum(weights[d] * dims[d] for d in avail) / wsum
            for d in avail:
                for k in used[d]:
                    contrib[k] = weights[d] / wsum * float(iw.get(k, 1.0)) / wts[d] * nv[k]
    return {"dims": dims, "n": cnt, "disponibles": avail, "global": g, "contributions": contrib, "dimensions_insuffisantes": insuff}


def competition_rank(scores):
    """scores : {iso3: valeur} → rangs 1 = score le plus libéral (100), ex æquo au même rang."""
    items = sorted(((v, k) for k, v in scores.items() if v is not None), key=lambda t: (-round(t[0], 9), t[1]))
    ranks, prev, rk = {}, None, 0
    for i, (v, k) in enumerate(items, 1):
        if prev is None or round(v, 9) != prev:
            rk = i; prev = round(v, 9)
        ranks[k] = rk
    return ranks


def reliability(data, iso3, defs, ind_dim, weights):
    cfg = data["dim"]["fiabilite"]; qual = data["dim"]["qualite_source"]
    obs = data["obs"].get(iso3, {})
    total = {d: sum(1 for k in defs if ind_dim[k] == d) for d in DIMS}
    avail = {d: sum(1 for k in obs if k in defs and ind_dim[k] == d) for d in DIMS}
    wt = sum(weights.values())
    C = sum(weights[d] * (avail[d] / total[d]) for d in DIMS if total[d]) / wt
    ks = [k for k in obs if k in defs]
    if ks:
        Q = sum(qual[defs[k]["source_type"]] for k in ks) / len(ks)
        ref = data["dim"]["annee_cible"]
        F = sum(max(0.0, 1 - (ref - obs[k]["annee"]) / 10.0) for k in ks) / len(ks)
        nres = sum(1 for k in ks if obs[k]["statut_validation"] != "valide")
        conteste = 1 if any(w in data["pays"][iso3]["statut_politique"].lower() for w in ("contest", "séparatiste", "annex", "non reconnu", "autoproclam")) else 0
        K = max(0.0, 1 - 0.10 * nres - 0.10 * conteste)
    else:
        Q = F = K = 0.0
    p = cfg["poids"]
    R = 100 * (p["couverture"] * C + p["qualite_source"] * Q + p["anciennete"] * F + p["comparabilite"] * K)
    n = cfg["niveaux"]
    niveau = "élevée" if R >= n["elevee"] else "moyenne" if R >= n["moyenne"] else "faible" if R >= n["faible"] else "très faible"
    return {"fiabilite": R, "niveau": niveau, "couverture": C, "qualite_source": Q, "anciennete": F, "comparabilite": K,
            "n_indicateurs": len(ks), "n_indicateurs_total": len(defs)}


def deep_merge(a, b):
    """Fusion récursive (b prioritaire) ; les listes « ajouter » sont réunies."""
    out = copy.deepcopy(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif k == "ajouter" and isinstance(v, list):
            out[k] = sorted(set(out.get(k, [])) | set(v))
        else:
            out[k] = copy.deepcopy(v)
    return out


def option_patch(decision, option_id):
    for o in decision.get("options", []):
        if o["id"] == option_id:
            return o.get("patch") or {}
    raise KeyError(f"{decision['id']} : option {option_id} inconnue")


def decisions_overrides(data, choix=None):
    """Surcharges cumulées.
    * sans `choix` : décisions au statut « approuvée », avec l'option retenue par l'utilisateur (méthode officielle) ;
    * `choix` = {id_decision: id_option} : scénario ; les décisions approuvées non citées gardent leur option retenue.
    """
    ov = {}
    for dcs in data.get("decisions", {}).get("decisions", []):
        opt = None
        if choix is not None and dcs["id"] in choix:
            opt = choix[dcs["id"]]
        elif dcs.get("statut") == "approuvée":
            opt = dcs.get("option_retenue")
        if opt:
            ov = deep_merge(ov, option_patch(dcs, opt))
    return ov


def scenario_recommande(data):
    """Choix correspondant à l'option recommandée de chaque décision non encore tranchée."""
    return {d["id"]: d["option_recommandee"] for d in data.get("decisions", {}).get("decisions", [])
            if d.get("statut") not in ("approuvée", "rejetée") and d.get("option_recommandee")}


def apply_overrides(data, overrides):
    """Copie de `data` dans laquelle la configuration est modifiée par `overrides` (aucune donnée n'est modifiée)."""
    if not overrides:
        return data
    d2 = dict(data); d2["dim"] = copy.deepcopy(data["dim"]); d2["ind"] = copy.deepcopy(data["ind"])
    if "poids_dimensions" in overrides:
        for dd in d2["dim"]["dimensions"]:
            dd["poids"] = float(overrides["poids_dimensions"].get(dd["id"], dd["poids"]))
    if "regles" in overrides:
        d2["dim"]["regles_couverture"] = deep_merge(rules_of(data), overrides["regles"])
    alts = {a["id"]: a for a in d2["ind"].get("alternatives_sensibilite", [])}
    for aid in overrides.get("ajouter", []):
        a = copy.deepcopy(alts[aid]); a.setdefault("source_type", "intergouvernementale")
        d2["ind"]["indicateurs"].append(a)
        d2["obs"] = {iso: dict(v) for iso, v in (d2["obs"]).items()}
        for iso, v in data["alt"].items():
            if aid in v:
                d2["obs"].setdefault(iso, {})[aid] = v[aid]
    byid = {i["id"]: i for i in d2["ind"]["indicateurs"]}
    for k, ch in overrides.get("indicateurs", {}).items():
        if k in byid:
            byid[k].update(copy.deepcopy(ch))
    return d2


def compute(data, method="minmax", weights=None, included=None, min_dims=None, require_a=None, overrides=None):
    """Calcule les scores. `overrides` : surcharges de configuration (scénario). Sans argument : méthode officielle
    (configuration de base + décisions approuvées)."""
    if overrides is None:
        overrides = decisions_overrides(data)
    data = apply_overrides(data, overrides)
    rules = rules_of(data)
    min_dims = rules["min_dimensions"] if min_dims is None else min_dims
    require_a = rules["exiger_dimension_A"] if require_a is None else require_a
    defs = indicator_defs(data)
    ind_dim = {k: v["dim"] for k, v in defs.items()}
    iw = {k: float(v.get("poids_interne", 1.0)) for k, v in defs.items()}
    weights = weights or dim_weights(data)
    norm, params = normalize(data, method, "obs", defs)
    res = {}
    for iso3 in data["pays"]:
        nv = norm.get(iso3, {})
        res[iso3] = score_country(nv, ind_dim, weights, included, min_dims, require_a, iw, rules["min_indicateurs"])
        res[iso3]["norm"] = nv
    ranks = competition_rank({k: v["global"] for k, v in res.items()})
    for k in res:
        res[k]["rang"] = ranks.get(k)
    return res, params, norm


def statut_couverture(r):
    n = sum(1 for d in DIMS if r["dims"][d] is not None)
    if n == 4:
        return "complet"
    if r["global"] is not None:
        return "partiel"
    return "insuffisant" if n >= 1 else "aucune donnée"


def build_output(data, overrides=None, label="officielle"):
    """Sortie complète. Sans `overrides` : méthode officielle (base + décisions approuvées)."""
    if overrides is None:
        overrides = decisions_overrides(data)
    res, params, norm = compute(data, overrides=overrides)
    data = apply_overrides(data, overrides)
    rules = rules_of(data)
    defs = indicator_defs(data)
    ind_dim = {k: v["dim"] for k, v in defs.items()}
    weights = dim_weights(data)
    n_ranked = sum(1 for r in res.values() if r["global"] is not None)
    rang_complets = competition_rank({k: r["global"] for k, r in res.items() if statut_couverture(r) == "complet"})
    approuvees = {d["id"]: d.get("option_retenue") for d in data.get("decisions", {}).get("decisions", []) if d.get("statut") == "approuvée"}
    out = {"version_methodologie": data["dim"]["version_methodologie"], "annee_cible": data["dim"]["annee_cible"], "methode": label,
           "decisions_approuvees": approuvees, "surcharges": overrides, "regles_couverture": rules,
           "indicateurs_inclus": sorted(defs), "poids_internes": {k: float(v.get("poids_interne", 1.0)) for k, v in sorted(defs.items())},
           "poids_dimensions": weights, "empreinte_jeu_de_donnees": dataset_hash(), "n_entites": len(res), "n_avec_score_global": n_ranked,
           "normalisation": {"methode": "minmax", "parametres": params}, "pays": {}}
    for iso3, p in sorted(data["pays"].items()):
        r = res[iso3]; rel = reliability(data, iso3, defs, ind_dim, weights)
        obs = data["obs"].get(iso3, {})
        statut = statut_couverture(r)
        absentes = [d for d in DIMS if r["dims"][d] is None]
        warn = []
        if statut == "partiel":
            warn.append(f"Score partiel : dimension(s) absente(s) {', '.join(absentes)} ; poids des dimensions disponibles renormalisés. Non directement comparable à un score complet.")
        if statut == "insuffisant":
            warn.append(f"Score global non calculé (règle : dimension A {'exigée' if rules['exiger_dimension_A'] else 'non exigée'}, au moins {rules['min_dimensions']} dimensions valides). Les scores de dimension disponibles restent affichés.")
        if statut == "aucune donnée":
            warn.append("Aucune observation disponible pour les indicateurs de la V1.")
        for d in DIMS:
            if r["dims"][d] is not None:
                tot = sum(1 for k in defs if ind_dim[k] == d)
                if r["n"][d] < tot:
                    warn.append(f"Dimension {d} calculée sur {r['n'][d]}/{tot} indicateurs.")
        for d in r["dimensions_insuffisantes"]:
            warn.append(f"Dimension {d} non calculée : {r['n'][d]} indicateur(s) disponible(s), minimum requis {rules['min_indicateurs'][d]}.")
        if p["statut_politique"] != "État souverain":
            warn.append("Statut : " + p["statut_politique"] + ".")
        reserves = [k for k, o in obs.items() if o["statut_validation"] != "valide"]
        if reserves:
            warn.append("Valeur(s) signalée(s) (extrême ou ancienne) : " + ", ".join(sorted(reserves)) + ".")
        out["pays"][iso3] = {
            "nom": p["nom_fr"], "nom_en": p["nom_en"], "iso2": p["iso2"], "region": p["region"], "groupe_revenu": p["groupe_revenu"],
            "type": p["type"], "statut_politique": p["statut_politique"],
            "global": None if r["global"] is None else round(r["global"], 6), "rang": r["rang"], "rang_complets": rang_complets.get(iso3),
            "dimensions": {d: (None if r["dims"][d] is None else round(r["dims"][d], 6)) for d in DIMS},
            "n_par_dimension": r["n"], "statut_couverture": statut, "dimensions_absentes": absentes,
            "couverture_indicateurs": round(sum(r["n"].values()) / len(defs), 6) if defs else 0.0,
            "contributions": {k: round(v, 6) for k, v in sorted(r["contributions"].items())},
            "fiabilite": {k: (round(v, 6) if isinstance(v, float) else v) for k, v in rel.items()},
            "indicateurs": {k: {"brut": o["valeur_brute"], "norm": (round(norm[iso3][k], 6) if k in norm.get(iso3, {}) else None),
                                "inclus": k in defs, "annee": o["annee"], "statut": o["statut_validation"],
                                "source": o["source"], "url": o["url_source"], "transformation": o["transformation"],
                                "limites": o["limites_comparabilite"], "collecte": o["date_collecte"], "revision": o["date_revision"]}
                            for k, o in sorted(obs.items())},
            "avertissements": warn}
    return out


def main():
    data = load()
    out = build_output(data)
    dst = os.path.join(PROC, "scores.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"{out['n_entites']} entités ; {out['n_avec_score_global']} avec score global ; empreinte {out['empreinte_jeu_de_donnees'][:16]}…")


if __name__ == "__main__":
    main()
