# Audit de l'ancienne grille (indice composite V1.0 / V1.1)

Archive complète : `archive/v1/` (code, configuration, corpus, données, documentation, HTML ; les 18 tests du moteur V1 réussissent depuis l'archive, vérifié le 2026-10-29) et `editions/v1.0`, `editions/v1.1`. Chiffres ci-dessous calculés par `tools/compare_v1.py` (`docs/comparaison_v1_v2.json`) et à partir de `editions/v1.1/scores.json`.

## Rappel de la méthode V1.1

19 indicateurs répartis en 4 dimensions (A libéralisme économique 45 %, B redistribution 20 %, C place de l'État 20 %, D libertés 15 %), choisis et orientés à partir d'une lecture de *Capitalisme et liberté* ; normalisation min-max sur les percentiles P5-P95 de l'échantillon ; moyenne simple par dimension ; score global = moyenne pondérée des dimensions disponibles, poids renormalisés ; 222 entités sur 237 avec un score global.

## Causes principales des évaluations aberrantes

1. **Scores globaux calculés sur très peu d'indicateurs et classés avec les autres.** La règle exigeait la dimension A et 2 dimensions, mais pas un nombre minimal d'indicateurs : 19 entités ont un score global calculé sur 2 à 4 indicateurs sur 19. Exemples : Chypre du Nord **2e** (76,8) sur 4 indicateurs tous issus de Freedom House (A6, D2-D4) ; Haut-Karabagh **dernier avec 0,0** sur les mêmes 4 indicateurs ; Nouvelle-Calédonie 35e sur 2 indicateurs. La renormalisation des poids faisait porter 100 % du score sur les dimensions présentes.
2. **Couverture très inégale selon les pays.** Les indicateurs fiscaux et de réglementation de l'OCDE (B2-B7, A2, A3) ne couvrent qu'une quarantaine d'économies : 29 entités sont évaluées sur 19 indicateurs, beaucoup d'autres sur 7 à 13. Deux pays ne sont donc pas jugés sur la même grille, ce qui avantage mécaniquement ceux qui échappent aux indicateurs de prélèvements.
3. **Normalisation dépendante de l'échantillon.** Bornes P5-P95 calculées sur les pays présents, valeurs hors bornes ramenées à 0 ou 100 : un score dépendait de la composition de l'échantillon, et plusieurs entités atteignaient les bornes (0,0 pour le Haut-Karabagh).
4. **Choix interprétatifs lourds et instables.** La sélection, l'orientation (« vers 0 » ou « vers 100 ») et la pondération des indicateurs relevaient d'interprétations du corpus ; un seul changement de traitement des prélèvements (V1.0 → V1.1) a déplacé le Danemark du 2e au 14e rang, la Suède du 8e au 31e, le Liban du 26e au 74e (Spearman 0,957 entre les deux versions).
5. **Mélange des dimensions.** Des sous-scores Freedom House servaient à la fois à la liberté économique (A6) et politique (D2-D4), et le score unique confondait liberté économique et liberté politique : Singapour (V1 : 16e) et Hong Kong (24e) apparaissaient proches de pays démocratiques alors que leurs situations politiques sont très différentes ; le repère V2 les sépare (Hong Kong X 85,5 / Y 14,2).
6. **Années hétérogènes** (fenêtre 2019-2023 indicateur par indicateur) sans avertissement par point.

## Ce que la V2 conserve, retire, archive

| Élément | Décision |
|---|---|
| Score global 0-100, dimensions A-D, pondérations, corpus Friedman, règles de fiabilité | retirés de l'interface ; archivés (`archive/v1/`) |
| Données brutes V1 (Banque mondiale, OCDE, Freedom House 2013-2024) | archivées ; fichiers OCDE fiscaux et Freedom House réutilisés à l'identique (même SHA-256) pour les données contextuelles et l'historique FH |
| Référentiel des 237 entités et statuts des territoires | conservé et complété (239 entités) |
| Anciennes éditions HTML et scores | conservées dans `editions/v1.0`, `editions/v1.1`, `archive/v1/dist/` |

## Comparaison descriptive avec la V2 (non une validation)

Sur les entités présentes dans les deux systèmes : corrélation de rang (Spearman) entre le score global V1.1 et X Fraser = 0,810 ; entre le score global V1.1 et Y V-Dem = 0,790 ; entre la dimension A V1.1 et X Fraser = 0,864 ; entre la dimension D V1.1 et Y V-Dem = 0,953. 162 entités ont à la fois un score V1 et deux coordonnées V2 ; 41 entités notées en V1 (surtout micro-États et territoires) n'ont aucune coordonnée V2, faute de couverture par Fraser et V-Dem : la V2 les montre comme non couvertes au lieu de leur attribuer un score.

Les valeurs V1 et V2 mesurent des objets différents et ne doivent pas être comparées comme une évolution.
