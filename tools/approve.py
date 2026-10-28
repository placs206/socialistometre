#!/usr/bin/env python3
"""Arbitrage des décisions méthodologiques (config/decisions.json) par l'utilisateur.

  python3 tools/approve.py --liste
  python3 tools/approve.py DEC-01 A3_B3_C2_D2 [--commentaire "…"]     approuver une option
  python3 tools/approve.py --rejeter DEC-03 [--commentaire "…"]        rejeter la proposition (statu quo)
  python3 tools/approve.py --import arbitrages.json                    appliquer un export de l'interface HTML

Chaque approbation : statut « approuvée », option retenue, date, empreinte de la configuration résultante ;
la version de méthodologie est incrémentée (1.1 → 1.2…) car la méthode officielle change ; la comparaison
avant/après est écrite dans docs/COMPARAISON_V<ancienne>_V<nouvelle>.md. Ensuite, relancer la chaîne :
  python3 tools/build_dataset.py && python3 engine/scoring.py && python3 tools/run_robustness.py \\
  && python3 tools/audit/diagnostic.py && python3 tools/audit/simulate.py && python3 tools/audit/make_audit_files.py \\
  && python3 tools/make_docs.py && python3 tools/build_html.py && python3 tools/make_edition.py
Rien n'est approuvé sans commande explicite de l'utilisateur.
"""
import argparse, datetime, hashlib, json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
import scoring as S  # noqa: E402
DEC_P = os.path.join(ROOT, "config", "decisions.json")
DIM_P = os.path.join(ROOT, "config", "dimensions.json")


def save(p, obj):
    json.dump(obj, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("decision", nargs="?"); ap.add_argument("option", nargs="?")
    ap.add_argument("--rejeter"); ap.add_argument("--import", dest="imp"); ap.add_argument("--liste", action="store_true")
    ap.add_argument("--commentaire", default="")
    a = ap.parse_args()
    reg = json.load(open(DEC_P, encoding="utf-8")); dims = json.load(open(DIM_P, encoding="utf-8"))
    byid = {d["id"]: d for d in reg["decisions"]}
    if a.liste:
        for d in reg["decisions"]:
            print(f"{d['id']:7} {d['statut']:10} retenue={d.get('option_retenue') or '—':14} recommandée={d['option_recommandee']:14} {d['titre']}")
            for o in d["options"]:
                print(f"          - {o['id']} : {o['libelle']}")
        return
    todo = []
    if a.imp:
        e = json.load(open(a.imp, encoding="utf-8"))
        if e.get("format") != "socialistometre-arbitrages":
            sys.exit("format de fichier inconnu")
        for k, v in e.get("decisions", {}).items():
            todo.append((k, v["option"], v.get("action", "approuver"), v.get("commentaire", "")))
    elif a.rejeter:
        todo.append((a.rejeter, None, "rejeter", a.commentaire))
    elif a.decision and a.option:
        todo.append((a.decision, a.option, "approuver", a.commentaire))
    else:
        ap.print_help(); return
    data0 = S.load()
    before, _, _ = S.compute(data0)
    old_v = dims["version_methodologie"]
    today = datetime.date.today().isoformat()
    changed = False
    for did, opt, action, com in todo:
        d = byid.get(did)
        if not d:
            sys.exit(f"décision inconnue : {did}")
        if action == "rejeter":
            d.update({"statut": "rejetée", "option_retenue": None, "decision_utilisateur": "rejetée", "date_decision": today, "commentaire_utilisateur": com})
            continue
        if action != "approuver":
            continue
        if opt not in [o["id"] for o in d["options"]]:
            sys.exit(f"{did} : option inconnue {opt}")
        d.update({"statut": "approuvée", "option_retenue": opt, "decision_utilisateur": "approuvée", "date_decision": today, "commentaire_utilisateur": com})
        changed = changed or bool(S.option_patch(d, opt))
    new_v = old_v
    if changed:
        maj, mi = old_v.split(".")[:2]; new_v = f"{maj}.{int(mi) + 1}"
        dims["version_methodologie"] = new_v
    for did, opt, action, _ in todo:
        byid[did]["version_methode"] = new_v
    data0["decisions"] = reg
    ov = S.decisions_overrides(data0)
    h = hashlib.sha256(json.dumps(ov, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    for did, _, _, _ in todo:
        byid[did]["empreinte_configuration"] = h
    save(DEC_P, reg); save(DIM_P, dims)
    data1 = S.load()
    after, _, _ = S.compute(data1)
    g0 = {k: r["global"] for k, r in before.items() if r["global"] is not None}
    g1 = {k: r["global"] for k, r in after.items() if r["global"] is not None}
    com_ = [k for k in g0 if k in g1]
    rho = S.spearman([g0[k] for k in com_], [g1[k] for k in com_]) if len(com_) > 2 else 1.0
    mv = sorted(com_, key=lambda k: -abs(g1[k] - g0[k]))[:25]
    lines = [f"# Comparaison V{old_v} → V{new_v} (changement méthodologique, {today})", "",
             "Décisions : " + ", ".join(f"{did} → {opt or 'rejetée'}" for did, opt, _, _ in todo), "",
             f"Scores globaux : {len(g0)} → {len(g1)} ; Spearman des rangs communs {rho:.4f} ; retirés : " + (", ".join(data1['pays'][k]['nom_fr'] for k in g0 if k not in g1) or "aucun"), "",
             "| Pays | Ancien score | Nouveau | Variation | Ancien rang | Nouveau rang |", "|---|---|---|---|---|---|"]
    lines += [f"| {data1['pays'][k]['nom_fr']} | {g0[k]:.1f} | {g1[k]:.1f} | {g1[k] - g0[k]:+.1f} | {before[k]['rang']} | {after[k]['rang']} |" for k in mv]
    if changed:
        open(os.path.join(ROOT, "docs", f"COMPARAISON_V{old_v}_V{new_v}.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:6]))
    print(f"\nMéthodologie {old_v} → {new_v}. Relancer la chaîne de calcul (voir l'en-tête de ce script) puis archiver l'édition.")


if __name__ == "__main__":
    main()
