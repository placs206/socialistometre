#!/usr/bin/env python3
"""Régénère docs/METHODOLOGIE.md à partir de la configuration, des principes et des résultats de tests."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = lambda p: json.load(open(os.path.join(ROOT, p), encoding="utf-8"))
ind, pr, rob, dm = L("config/indicateurs.json"), L("corpus/principes.json")["principes"], L("docs/robustesse.json")["tests"], L("config/dimensions.json")
v = dm["version_methodologie"]
cnt = {d: sum(1 for i in ind["indicateurs"] if i["dim"] == d) for d in "ABCD"}
rows = "\n".join(f"| {i['id']} | {i['dim']} | {i['nom']} | {'+1' if i['orientation'] > 0 else '−1'} | {', '.join(i['principes'])} | {i['source']} ({i['source_type']}) |" for i in ind["indicateurs"])
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
| Id | Dim. | Indicateur | Sens | Principes | Source |
|---|---|---|---|---|---|
{rows}

Détails (lien avec le texte, limites, chevauchements) : `config/indicateurs.json`.

## Exclusions documentées
{exc}

## Calcul
1. Observation : dernière valeur non nulle dans la fenêtre 2019–2023 (année réelle conservée, aucune imputation).
2. Normalisation « minmax » : `t = clip((x−bas)/(haut−bas),0,1)` ; score = 100·t (sens +1) ou 100·(1−t) (sens −1). Bornes fixes pour échelles naturelles ; P5–P95 mondiaux pour A1, B3, B5, B6, B7, C2, C3.
3. Dimension = moyenne simple des indicateurs disponibles.
4. Global = Σ poids·dimension / Σ poids sur les dimensions disponibles. **Règle** : dimension A exigée et ≥ 2 dimensions, sinon pas de score global (les scores de dimension restent affichés).
5. Fiabilité = 100·(0,4·couverture + 0,2·qualité source + 0,2·fraîcheur + 0,2·comparabilité), affichée séparément.
6. Statuts : complet (4 dimensions), partiel (score global, <4 dimensions), insuffisant (pas de score global), aucune donnée.

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
