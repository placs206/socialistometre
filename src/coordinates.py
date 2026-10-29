#!/usr/bin/env python3
"""Moteur des coordonnées (X, Y) — seule implémentation des règles de sélection (le HTML ne fait que lire le résultat).

Entrées : data/processed/observations.csv, data/reference/pays.csv, config/parametres.json, config/sources.json.
Sortie  : data/processed/coordonnees.json (déterministe : pas de date, pas d'aléa, clés triées).

Règles (config/parametres.json) :
* coordonnée = valeur_0_100 de l'indicateur principal de la source choisie (transformation affine officielle, src/transform.py) ;
* mode « recent » : année de référence la plus récente de la source pour l'entité ; mode « annee:N » : année N exactement ;
* aucune moyenne entre sources, aucun bonus/malus, aucune valeur inventée ; absence ⇒ coordonnée null ;
* scénario officiel = Fraser (X) × V-Dem (Y), mode « recent » ; les autres scénarios sont des modes de comparaison.
Usage : python3 -m src.coordinates
"""
import datetime
import hashlib
import os

from src.common import PROC, REF, config, read_csv, sha256_file, write_json

P = config("parametres.json")


def _date(s):
    return datetime.date.fromisoformat(s)


def mid(o):
    a, b = _date(o["periode_debut"]), _date(o["periode_fin"])
    return a + (b - a) / 2


def gap_years(ox, oy):
    return round(abs((mid(ox) - mid(oy)).days) / 365.25, 2)


def load_principal():
    """{(source, indicateur): {iso3: [obs triées par année]}} pour les indicateurs principaux."""
    out = {}
    for o in read_csv(os.path.join(PROC, "observations.csv")):
        if o["role"] != "principal":
            continue
        o["annee_reference"] = int(o["annee_reference"])
        o["valeur_0_100"] = float(o["valeur_0_100"])
        out.setdefault((o["source"], o["indicateur"]), {}).setdefault(o["iso3"], []).append(o)
    for d in out.values():
        for lst in d.values():
            lst.sort(key=lambda o: (o["annee_reference"], o["edition"]))
            years = [o["annee_reference"] for o in lst]
            assert len(years) == len(set(years)), f"deux observations la même année : {lst[0]['iso3']} {lst[0]['source']}"
    return out


def select(series, iso3, mode):
    lst = series.get(iso3, [])
    if not lst:
        return None
    if mode == "recent":
        return lst[-1]
    n = int(mode.split(":")[1])
    m = [o for o in lst if o["annee_reference"] == n]
    return m[0] if m else None


def ref(o):
    return None if o is None else {"v": o["valeur_0_100"], "off": o["valeur_officielle"], "ed": o["edition"],
                                   "an": o["annee_reference"], "deb": o["periode_debut"], "fin": o["periode_fin"],
                                   "hors": o["statut_validation"] == "hors_echelle_officielle"}


def scenario(obs, pays, xs, ys, mode):
    pts = {}
    for iso3 in sorted(pays):
        ox = select(obs[(xs["source"], xs["indicateur"])], iso3, mode)
        oy = select(obs[(ys["source"], ys["indicateur"])], iso3, mode)
        statut = "complet" if ox and oy else "x_seulement" if ox else "y_seulement" if oy else "aucune"
        pts[iso3] = {"x": ref(ox), "y": ref(oy), "ecart": gap_years(ox, oy) if ox and oy else None, "statut": statut}
    return pts


def divergences(obs, pays, seuil):
    out = {}
    pairs = {"economique": (("fraser", "efw_summary"), ("heritage", "ief_overall")),
             "politique": (("vdem", "v2x_libdem"), ("freedomhouse", "fiw_total"))}
    for iso3 in sorted(pays):
        d = {}
        for axe, (a, b) in pairs.items():
            oa, ob = select(obs[a], iso3, "recent"), select(obs[b], iso3, "recent")
            if oa and ob:
                diff = round(oa["valeur_0_100"] - ob["valeur_0_100"], 6)
                d[axe] = {"a": a[0], "b": b[0], "diff": diff, "an_a": oa["annee_reference"], "an_b": ob["annee_reference"],
                          "forte": abs(diff) >= seuil}
        if d:
            out[iso3] = d
    return out


def dataset_hash():
    h = hashlib.sha256()
    for rel in ("data/processed/observations.csv", "data/processed/contexte.csv", "data/reference/pays.csv",
                "data/reference/correspondances.csv", "config/sources.json", "config/parametres.json", "config/contexte.json"):
        h.update(rel.encode())
        h.update(bytes.fromhex(sha256_file(os.path.join(os.path.dirname(PROC), "..", rel))))
    return h.hexdigest()


def compute():
    obs = load_principal()
    pays = {p["iso3"]: p for p in read_csv(os.path.join(REF, "pays.csv"))}
    off = P["configuration_officielle"]
    xs_opts, ys_opts = P["options_comparaison"]["axe_x"], P["options_comparaison"]["axe_y"]
    years = sorted({o["annee_reference"] for xs in xs_opts for lst in obs[(xs["source"], xs["indicateur"])].values() for o in lst})
    modes = ["recent"] + [f"annee:{y}" for y in years]
    scen = {}
    for xs in xs_opts:
        for ys in ys_opts:
            for mode in modes:
                sid = f"{xs['source']}|{ys['source']}|{mode}"
                officiel = xs == off["axe_x"] and ys == off["axe_y"] and mode == off["mode_periode"]
                pts = scenario(obs, pays, xs, ys, mode)
                cnt = {k: sum(1 for p in pts.values() if p["statut"] == k) for k in ("complet", "x_seulement", "y_seulement", "aucune")}
                scen[sid] = {"x": xs, "y": ys, "mode": mode, "officiel": officiel, "comptes": cnt, "points": pts}
    assert sum(s["officiel"] for s in scen.values()) == 1
    res = {"version_methodologie": P["version_methodologie"], "configuration_officielle": off,
           "scenario_officiel": next(k for k, s in scen.items() if s["officiel"]),
           "seuil_ecart_annees": P["seuil_ecart_annees"], "seuil_divergence_points": P["seuil_divergence_points"],
           "empreinte_jeu_de_donnees": dataset_hash(), "scenarios": scen,
           "divergences": divergences(obs, pays, P["seuil_divergence_points"])}
    return res


if __name__ == "__main__":
    r = compute()
    write_json(os.path.join(PROC, "coordonnees.json"), r, compact=True)
    s = r["scenarios"][r["scenario_officiel"]]
    print("scénario officiel", r["scenario_officiel"], s["comptes"], "empreinte", r["empreinte_jeu_de_donnees"][:16])
