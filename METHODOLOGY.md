# Méthodologie V2.0.0 (2026-10-29)

Rupture avec la V1 : l'indice composite 0-100 (4 dimensions pondérées 45/20/20/15, indicateurs justifiés par *Capitalisme et liberté*) est abandonné comme résultat principal. Les anciennes valeurs et les nouvelles coordonnées **ne sont pas comparables** (voir `docs/AUDIT_ANCIENNE_GRILLE.md`).

## 1. Résultat principal

Pour chaque entité *i* : un point (X*i*, Y*i*).

- **X — liberté économique** = indice synthétique *Economic Freedom of the World* (Fraser Institute), échelle officielle 0-10.
- **Y — libéralisme politique** = *Liberal Democracy Index* `v2x_libdem` (V-Dem), échelle officielle 0-1.

Les deux axes sont indépendants : un pays peut être haut sur l'un et bas sur l'autre (ex. Hong Kong : X 85,5 ; Y 14,2). Le milieu de l'échelle n'est pas un seuil idéologique ; les quadrants ne sont pas nommés.

## 2. Transformation d'échelle (seule opération appliquée aux scores)

Affine, fixe, réversible, bornes issues de la documentation officielle de l'édition (jamais de l'échantillon) — `src/transform.py` :

    v100 = (v − min) × 100 / (max − min)        v = min + v100 × (max − min) / 100

| Indice | Échelle officielle | Transformation | Réciproque |
|---|---|---|---|
| Fraser EFW (synthétique et 5 domaines) | 0-10 | × 10 | ÷ 10 |
| V-Dem LDI, composantes, bornes HPD | 0-1 | × 100 | ÷ 100 |
| Heritage IEF (global et 12 composantes) | 0-100 | identité | identité |
| Freedom House total | 0-100 | identité | identité |
| Freedom House droits politiques / libertés civiles | 0-40 / 0-60 | × 2,5 / × 100/60 | ÷ 2,5 / × 0,6 |

Calcul en décimal exact (arrondi à 10⁻⁶ seulement pour /60). Aucune troncature : les scores Freedom House officiellement négatifs (question discrétionnaire B, jusqu'à −4 points sur les droits politiques ; ex. total −1 pour les territoires ukrainiens occupés en 2025) restent négatifs et sont signalés « hors échelle nominale ». Interdits : normalisation min-max sur l'échantillon, conversion de rangs en scores, bonus/malus, moyenne entre sources.

## 3. Sélection des observations (`src/coordinates.py`, seule implémentation)

- **Mode « plus récente » (officiel)** : pour chaque entité et chaque source, l'observation dont l'année de référence est la plus récente parmi les éditions importées.
- **Mode « année commune N »** : l'observation dont l'année de référence vaut exactement N ; sinon absence. Années proposées : 2023 (Fraser, V-Dem, Freedom House FIW 2024) et 2025 (Heritage, V-Dem, Freedom House FIW 2026). Heritage 2026 a pour année de référence 2025 = fin de sa période (2e sem. 2024 – 1er sem. 2025), toujours affichée.
- **Écart de période** = distance en années entre les milieux des périodes mesurées par X et Y. Au-delà du seuil d'affichage (1 an par défaut, modifiable dans l'interface), le point est dessiné creux et signalé : ce n'est pas une photographie simultanée. En mode officiel, l'écart est de 2 ans pour toutes les entités (Fraser 2023, V-Dem 2025).
- **Absence** : coordonnée `null`, jamais zéro, jamais estimée, jamais reportée d'une autre année. L'entité figure dans le tableau des données incomplètes.

## 4. Indices de comparaison

Heritage (X) et Freedom House (Y) ne sont jamais ajoutés ni moyennés aux sources principales. L'interface permet de les substituer dans un **mode comparaison** distinctement signalé (bandeau, libellé « non officiel et non enregistré », bouton de retour). Les 12 scénarios (2 sources X × 2 sources Y × 3 modes) sont précalculés en Python ; le HTML ne fait que les lire.

**Divergence** = différence en points 0-100 entre les deux indices d'un même axe (dernière année de chacun), descriptive. Seuil d'affichage : 15 points. Attention : Freedom House est en moyenne nettement plus élevé que l'indice V-Dem (différence médiane V-Dem − FH : −15,8 points), car le LDI combine multiplicativement composantes électorale et libérale ; les niveaux ne sont pas interchangeables et le projet ne désigne aucun organisme comme correct.

## 5. Données contextuelles

Charges et recettes publiques, prélèvements obligatoires, coin fiscal sur le travail, taux marginal supérieur, consommation publique, cotisations sociales, PIB par habitant (Banque mondiale, OCDE ; dernière valeur 2019-2025). Affichées à part dans les fiches ; **aucun poids** dans les coordonnées (testé : `test_contexte_sans_effet_sur_les_coordonnees`). Ce ne sont pas des mesures du « socialisme ».

## 6. Correspondance géographique

Référentiel : 239 entités (`data/reference/pays.csv`), codes ISO 3166-1 alpha-3, codes internes `X-…` pour les territoires sans code ISO, région Banque mondiale (de l'État de rattachement pour les territoires). Chaque entité source est rattachée explicitement (`data/reference/correspondances.csv`, méthodes `code_identique`, `nom_identique`, `manuel`) ; la construction échoue si une entité n'est pas rattachée. Cas documentés : V-Dem « Palestine/West Bank » → Cisjordanie (X-WBK) et non PSE (Cisjordanie + Gaza) ; Freedom House 2026 regroupe Crimée et Donbass oriental en « Russian-occupied territories of Ukraine » (X-RUA, frontière différente des séries antérieures) et ne publie plus le Haut-Karabagh ; Zanzibar et Somaliland codés séparément par V-Dem.

## 7. Contestations

Une contestation (formulaire de la fiche, stockée dans le navigateur, exportable ; ou `data/contestations/contestations.csv` dans le dépôt) documente un désaccord et ne modifie jamais une valeur. Seule une correction publiée par l'organisme, importée dans une nouvelle édition versionnée, peut changer une donnée.

## 8. Versions

Toute modification des sources principales, éditions, échelles, règles de sélection ou de la configuration officielle crée une nouvelle version de `config/parametres.json` et une nouvelle édition (`tools/make_edition.py`). Comparaison historique : à méthodologie constante via le mode « année commune » ; un changement de méthode est documenté dans `CHANGELOG.md`.
