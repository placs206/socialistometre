#!/usr/bin/env python3
"""Régénère docs/METHODOLOGIE.md à partir de la configuration, des principes et des résultats de tests."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
ind, pr, rob, dm = L("config/indicateurs.json"), L("corpus/principes.json")["principes"], L("docs/robustesse.json")["tests"], L("config/dimensions.json")
import sys; sys.path.insert(0, os.path.join(ROOT, "engine")); import scoring as S  # noqa: E402
_data = S.load(); RULES = S.rules_of(S.apply_overrides(_data, S.decisions_overrides(_data)))
DEC = L("config/decisions.json")["decisions"]
decs = "\n".join(f"| {d['id']} | {d['titre']} | {d['categorie']} ({d['categorie_libelle']}) | {d['nature']} | {d['option_recommandee']} | {d['statut']}{' → ' + d['option_retenue'] if d.get('option_retenue') else ''} |" for d in DEC)
v = dm["version_methodologie"]
cnt = {d: sum(1 for i in ind["indicateurs"] if i["dim"] == d) for d in "ABCD"}
rows = "\n".join(f"| {i['id']} | {i['dim']} | N{i.get('niveau_preuve', '?')} | {i['nom']} | {'+1' if i['orientation'] > 0 else '−1'} | {', '.join(i['principes'])} | {i['source']} ({i['source_type']}) |" for i in ind["indicateurs"])
exc = "\n".join(f"- **{e['candidat']}** ({e.get('principe', '—')}) : {e['raison']}" for e in ind["exclus"])
prs = "\n".join(f"- **{p['id']}** — {p['nom']} (p. {', '.join(str(r['page']) for r in p['refs'])})" for p in pr)
tr = "\n".join(f"| {t['id']} | {t['nom']} | {'oui' if t['critique'] else 'non'} | {t['statut']} |" for t in rob)
open(os.path.join(ROOT, "docs", "METHODOLOGIE.md"), "w", encoding="utf-8").write(f"""# Méthodologie V{v}

Indice mondial continu, 0 (pôle socialisant) → 100 (pôle libéral), construit **exclusivement** à partir de *Capitalisme et liberté* (M. Friedman, trad. Leduc.s 2010). Il ne s'agit pas d'un indice publié par Friedman : chaque indicateur est justifié par un principe vérifié dans le texte, puis mesuré par une source institutionnelle.

## Dimensions et poids (fixes)
A Libéralisme économique 45 % · B Redistribution et protection sociale 20 % · C Place de l'État dans l'économie 20 % · D Libertés individuelles et politiques 15 %.

## Principe de lecture des prélèvements (V1.1)
Impôts, taxes et cotisations sociales sont tous des **prélèvements** : aucune distinction n'est faite selon leur nom ou l'usage des fonds. Les prélèvements sont mesurés en plusieurs catégories : total (B5), revenus des personnes et travail en % du PIB (B6), taux de taxation du travail — coin fiscal (B7), taux marginal supérieur de l'impôt sur le revenu (B2), taux de l'impôt sur les sociétés (B3).

## Principes de Friedman retenus (citations vérifiées, pagination imprimée)
{prs}

Les principes P16 (règle monétaire) et P17 (changes flottants) sont établis mais non mesurés (aucune série institutionnelle comparable retenue).

## Indicateurs admis ({len(ind['indicateurs'])} : A={cnt['A']}, B={cnt['B']}, C={cnt['C']}, D={cnt['D']})
| Id | Dim. | Niveau de preuve | Indicateur | Sens | Principes | Source |
|---|---|---|---|---|---|---|
{rows}

Niveaux de preuve (audit 2026-10-28) : N1 mesure directe · N2 proxy validé · N3 proxy faible (ne doit pas compter sans approbation explicite de l'utilisateur : voir DEC-03, DEC-04). Dictionnaire complet : `INDICATOR_DICTIONARY.csv`.

Détails (lien avec le texte, limites, chevauchements) : `config/indicateurs.json`.

## Exclusions documentées
{exc}

## Calcul
1. Observation : dernière valeur non nulle dans la fenêtre 2019–2023 (année réelle conservée, aucune imputation).
2. Normalisation « minmax » : `t = clip((x−bas)/(haut−bas),0,1)` ; score = 100·t (sens +1) ou 100·(1−t) (sens −1). Bornes fixes pour échelles naturelles ; P5–P95 mondiaux pour A1, B3, B5, B6, B7, C2, C3.
3. Dimension = moyenne des indicateurs disponibles, pondérée par les poids internes (tous à 1 dans la méthode officielle) ; une dimension n'est calculée que si elle dispose d'au moins {', '.join(f"{d} : {n}" for d, n in RULES['min_indicateurs'].items())} indicateur(s).
4. Global = Σ poids·dimension / Σ poids sur les dimensions disponibles. **Règle** : {'dimension A exigée et ' if RULES['exiger_dimension_A'] else ''}≥ {RULES['min_dimensions']} dimensions, sinon pas de score global (les scores de dimension restent affichés). Contribution d'un indicateur = (w_d/Σw_d)·(w_i/Σw_i)·score_i ; Σ contributions = score global.
5. Fiabilité = 100·(0,4·couverture + 0,2·qualité source + 0,2·fraîcheur + 0,2·comparabilité), affichée séparément.
6. Statuts : complet (4 dimensions), partiel (score global, <4 dimensions), insuffisant (pas de score global), aucune donnée.

## Registre des décisions (audit du 2026-10-28)
La méthode officielle = configuration de base + décisions au statut « approuvée » (`config/decisions.json`, `DECISION_REGISTER.csv`). Les autres décisions ne servent qu'aux scénarios, dont le « scénario recommandé » (non approuvé). Approbation : `python3 tools/approve.py DEC-xx option` ou `--import` d'un fichier exporté de l'interface.

| Id | Décision | Catégorie | Nature | Option recommandée | Statut |
|---|---|---|---|---|---|
{decs}

## Validation d'une observation
`valide` ; `valide_avec_reserve` (valeur extrême > 5 MAD ou année < 2021) ; valeurs hors plage rejetées et journalisées (`data/processed/anomalies.csv`).

## Versionnement
Toute modification d'indicateur, de pondération ou de normalisation = nouvelle version, archivée dans `editions/`. Les comparaisons historiques distinguent (1) évolution à méthodologie constante, (2) effet d'un changement méthodologique (`docs/COMPARAISON_V1.0_V1.1.md`).

## Tests
| Id | Test | Critique | Résultat |
|---|---|---|---|
{tr}

Détails : `docs/ROBUSTESSE.md`.
""")
