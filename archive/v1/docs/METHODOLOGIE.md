# Méthodologie V1.1

Indice mondial continu, 0 (pôle socialisant) → 100 (pôle libéral), construit **exclusivement** à partir de *Capitalisme et liberté* (M. Friedman, trad. Leduc.s 2010). Il ne s'agit pas d'un indice publié par Friedman : chaque indicateur est justifié par un principe vérifié dans le texte, puis mesuré par une source institutionnelle.

## Dimensions et poids (fixes)
A Libéralisme économique 45 % · B Redistribution et protection sociale 20 % · C Place de l'État dans l'économie 20 % · D Libertés individuelles et politiques 15 %.

## Principe de lecture des prélèvements (V1.1)
Impôts, taxes et cotisations sociales sont tous des **prélèvements** : aucune distinction n'est faite selon leur nom ou l'usage des fonds. Les prélèvements sont mesurés en plusieurs catégories : total (B5), revenus des personnes et travail en % du PIB (B6), taux de taxation du travail — coin fiscal (B7), taux marginal supérieur de l'impôt sur le revenu (B2), taux de l'impôt sur les sociétés (B3).

## Principes de Friedman retenus (citations vérifiées, pagination imprimée)
- **P01** — Le gouvernement fixe les règles du jeu, arbitre et fait respecter les contrats ; ses fonctions sont nettement limitées (p. 84, 84)
- **P02** — Libre-échange : droits de douane et surtout quotas sont des atteintes à la liberté d'échange (p. 85, 125)
- **P03** — Contrôle des prix et des salaires, salaires minimaux légaux : atteinte au fonctionnement du marché (p. 85, 85, 297)
- **P04** — Les patentes (licences) professionnelles restreignent la liberté de choix de métier et ne se justifient pas par les principes libéraux (p. 222, 225)
- **P05** — Les monopoles et cartels créés ou soutenus par l'État limitent arbitrairement les échanges volontaires (p. 207)
- **P06** — La réglementation détaillée des industries n'a, en général, pas de justification (p. 85)
- **P07** — La fourniture publique (nationalisation) de l'enseignement est bien plus difficile à justifier que son financement public (p. 156, 156)
- **P08** — Bons scolaires : financement public, choix des parents, fourniture par des établissements privés ou à but non lucratif agréés (p. 157, 162)
- **P09** — La sécurité sociale obligatoire (retraite forcée, achat d'une annuité à l'État) restreint la liberté individuelle (p. 85, 283)
- **P10** — Impôt sur le revenu : taux uniforme plutôt que progressif ; un impôt progressif dont le seul but est de redistribuer est difficilement justifiable (p. 270, 270)
- **P11** — Abolition de l'impôt sur les revenus des sociétés, les revenus étant imputés aux actionnaires (p. 270)
- **P12** — Lutte contre la pauvreté par un impôt négatif sur le revenu, en espèces, au lieu de la multitude de programmes spécifiques (p. 297, 298)
- **P13** — Liberté d'expression, de publication et de réunion ; la liberté de défendre des causes impopulaires (p. 62, 85, 60)
- **P14** — Liberté économique et liberté politique : relation complexe, « nullement unilatérale » (p. 51)
- **P15** — Coordination par l'échange volontaire plutôt que par la coercition centralisée (p. 56, 55)
- **P16** — Règle monétaire (croissance fixée de la masse monétaire) plutôt que pouvoir discrétionnaire (p. 109)
- **P17** — Taux de change flottants, déterminés par des transactions privées (p. 126)
- **P18** — Le poids de l'État se mesure à la part du revenu national qu'il absorbe ; l'accroissement de cette part est l'étatisme que combat Friedman (p. 35, 35)
- **P19** — La cotisation de sécurité sociale est une taxe qui frappe les salaires : elle compte parmi les prélèvements sur le travail (p. 283)
- **P20** — Un impôt fortement progressif sur le revenu est un obstacle sérieux à l'utilisation efficace des ressources ; il faut diminuer drastiquement les taux les plus élevés (p. 215)

Les principes P16 (règle monétaire) et P17 (changes flottants) sont établis mais non mesurés (aucune série institutionnelle comparable retenue).

## Indicateurs admis (19 : A=6, B=6, C=3, D=4)
| Id | Dim. | Indicateur | Sens | Principes | Source |
|---|---|---|---|---|---|
| A1 | A | Droit de douane appliqué, moyenne simple, tous produits | −1 | P02 | Banque mondiale (WDI) ← UNCTAD TRAINS / OMC (intergouvernementale) |
| A2 | A | Réglementation des services professionnels (avocats, comptables, architectes, ingénieurs, agents immobiliers) | −1 | P04, P05 | OCDE – Product Market Regulation (PMR, OCDE et OCDE-Banque mondiale), édition 2023 (intergouvernementale) |
| A3 | A | Contrôles et réglementation des prix de détail | −1 | P03 | OCDE – Product Market Regulation (PMR), édition 2023 (intergouvernementale) |
| A4 | A | État de droit (exécution des contrats, droits de propriété, police, tribunaux) | +1 | P01 | Banque mondiale – Worldwide Governance Indicators (WGI) (recherche_institutionnelle) |
| A5 | A | Qualité de la réglementation (capacité à promouvoir le secteur privé) | +1 | P05, P06 | Banque mondiale – Worldwide Governance Indicators (WGI) (recherche_institutionnelle) |
| A6 | A | Droit de posséder des biens et de créer une entreprise privée | +1 | P15, P01 | Freedom House – Freedom in the World 2024, indicateur G2 (année civile 2023) (ong) |
| B2 | B | Taux marginal supérieur statutaire de l'impôt sur le revenu des personnes | −1 | P10 | OCDE – Base de données fiscales (Personal income tax, top statutory rate) (intergouvernementale) |
| B3 | B | Taux statutaire combiné de l'impôt sur les sociétés | −1 | P11 | OCDE – Corporate Tax Statistics (CIT, taux combiné, ensemble des administrations) (intergouvernementale) |
| B4 | B | Salaire minimum légal relatif au salaire médian des travailleurs à temps plein | −1 | P03 | OCDE – Statistiques sur les salaires minimaux (MIN2AVE, médiane) (intergouvernementale) |
| B5 | B | Prélèvements obligatoires totaux (impôts, taxes et cotisations sociales, sans distinction) en % du PIB | −1 | P18 | OCDE – Global Revenue Statistics (administrations publiques, total des recettes fiscales et cotisations) (intergouvernementale) |
| B6 | B | Prélèvements sur les revenus des personnes et le travail (impôt sur le revenu, cotisations sociales, taxes sur les salaires) en % du PIB | −1 | P19, P20 | OCDE – Global Revenue Statistics (codes 1100 + 2000 + 3000) (intergouvernementale) |
| B7 | B | Coin fiscal moyen sur le travail : impôt sur le revenu + cotisations salariales et patronales, en % du coût total du travail (célibataire sans enfant, salaire moyen) | −1 | P19, P20 | OCDE – Taxing Wages (indicateurs comparatifs, AV_TW, célibataire sans enfant, 100 % du salaire moyen) (intergouvernementale) |
| C1 | C | Qualité et étendue de la propriété publique des entreprises | −1 | P07 | OCDE – Product Market Regulation (PMR), édition 2023 (intergouvernementale) |
| C2 | C | Part des élèves du primaire scolarisés dans des établissements privés | +1 | P07, P08 | Banque mondiale (WDI) ← UNESCO ISU (intergouvernementale) |
| C3 | C | Consommation finale des administrations publiques en % du PIB | −1 | P01 | Banque mondiale (WDI) ← comptes nationaux (intergouvernementale) |
| D1 | D | Voix et responsabilité (participation, liberté d'expression et d'association, médias libres) | +1 | P13, P14 | Banque mondiale – Worldwide Governance Indicators (WGI) (recherche_institutionnelle) |
| D2 | D | Droits politiques (processus électoral, pluralisme politique, fonctionnement du gouvernement) | +1 | P14 | Freedom House – Freedom in the World 2024 (A+B+C, année civile 2023) (ong) |
| D3 | D | Liberté d'expression et de croyance (médias, religion, liberté académique, discussion privée) | +1 | P13 | Freedom House – Freedom in the World 2024, sous-score D (année civile 2023) (ong) |
| D4 | D | Droits d'association et d'organisation (réunion, ONG, syndicats) | +1 | P13 | Freedom House – Freedom in the World 2024, sous-score E (année civile 2023) (ong) |

Détails (lien avec le texte, limites, chevauchements) : `config/indicateurs.json`.

## Exclusions documentées
- **Inflation (FP.CPI.TOTL.ZG)** (P16) : L'inflation est un résultat, non une mesure de la règle monétaire institutionnelle défendue au chap. 3 ; fortement influencée par des chocs externes.
- **Régime de change flottant** (P17) : Pas de série institutionnelle comparable accessible et vérifiée dans cette V1.
- **Coefficient de Gini / pauvreté (SI.POV.GINI)** (P12) : Friedman ne fait pas de la réduction des inégalités un objectif ; il propose de lutter contre la pauvreté. Une inégalité faible ou forte n'a donc pas d'orientation 0/100 justifiable dans le corpus.
- **Subventions et autres transferts en % des dépenses (GC.XPN.TRFT.ZS)** (P12) : Agrège des subventions aux producteurs (condamnées p. 85) et des transferts en espèces aux ménages (cohérents avec l'impôt négatif, p. 297) : direction non attribuable.
- **Recettes fiscales en % du PIB (GC.TAX.TOTL.GD.ZS)** (P01) : Redondant avec C3 ; le niveau global de prélèvement ne documente pas un principe précis du corpus (chap. 10 traite de la structure de l'impôt).
- **Doing Business (Banque mondiale) : délai/coût de création d'entreprise, permis** (P05) : Rapport interrompu en 2021 après des irrégularités de données ; séries non mises à jour.
- **Indices Heritage / Fraser (liberté économique)** (—) : Accès impossible au moment de la collecte (HTTP 403) et risque de circularité : indices construits sur des priors pro-marché ; non institutionnels.
- **Taux marginal supérieur de l'IR hors OCDE** (P10) : Pas de série institutionnelle internationale accessible.
- **Part de l'État dans la propriété des entreprises (hors OCDE)** (P07) : Aucune série institutionnelle mondiale comparable accessible.
- **Impôt négatif sur le revenu / transferts en espèces universels** (P12) : Aucune base de données internationale comparable de l'existence d'un impôt négatif.
- **Licences professionnelles : médecine** (P04) : Aucun indicateur de licence médicale comparable à l'échelle mondiale ; seul le groupe de 5 professions PMR est utilisé (A2).
- **B1 (V1.0) : cotisations sociales en % des recettes publiques (Banque mondiale)** (P09) : Retiré en V1.1 : il traitait les cotisations sociales à part des autres prélèvements (et favorisait les pays finançant la protection sociale par l'impôt général). Friedman lui-même appelle la cotisation « une taxe […] qui frappe les salaires » (p. 283) ; impôts, taxes et cotisations sont désormais regroupés sous « prélèvements » (B5, B6, B7).

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
| T01 | Recalcul mathématique indépendant (numpy) de toutes les valeurs normalisées, dimensions et scores globaux | oui | RÉUSSI |
| T02 | Détection des doublons et incohérences (clés, identifiants, noms, années, traçabilité, erreurs du journal) | oui | RÉUSSI |
| T03 | Données brutes : empreintes SHA-256 du manifeste et relecture indépendante d'un échantillon (120 obs.) | oui | RÉUSSI |
| T04 | Données brutes et normalisées : plage [0,100], monotonie et sens d'orientation de chaque indicateur | oui | RÉUSSI |
| T05 | Analyse de sensibilité aux pondérations (±10 points par dimension, poids égaux, 2 000 tirages Dirichlet) | non | AVERTISSEMENT |
| T06 | Recalcul en retirant un indicateur à la fois (un recalcul par indicateur) | non | AVERTISSEMENT |
| T07 | Comparaison de plusieurs méthodes de normalisation (rang, z-score logistique, percentiles partout, P10-P90) | non | AVERTISSEMENT |
| T08 | Stabilité des rangs et des scores (600 rééchantillonnages : 80 % des indicateurs + poids perturbés) | non | RÉUSSI |
| T09 | Comportement en présence de données manquantes (masquage aléatoire de 1/3 des indicateurs ; règle « dimension A exigée » ; avertissements) | oui | RÉUSSI |
| T10 | Variantes d'indicateurs (tarif pondéré ; scolarisation privée secondaire) et redondances intra-dimension | non | RÉUSSI |
| T11 | Corrélations de rang entre dimensions (pays à score complet) — documentation de la relation liberté économique / liberté politique (Friedman, p. 51) | non | INFORMATIF |
| T12 | Reproductibilité d'une édition : reconstruction complète depuis data/raw (jeu de données + scores) et comparaison d'empreintes | oui | RÉUSSI |

Détails : `docs/ROBUSTESSE.md`.
