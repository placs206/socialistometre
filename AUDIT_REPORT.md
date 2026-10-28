# Audit critique du Socialistomètre V1.1 — rapport de synthèse

Audit du 28 octobre 2026, réalisé sur le dépôt `placs206/socialistometre` (commit `747fef8`, édition V1.1, données 2023, 237 entités dont 222 avec un score global). Tous les chiffres de ce rapport sont produits par les scripts du dépôt et peuvent être recalculés (voir la section « Reproduire »).

**Conclusion en une phrase.** Le code calcule exactement ce que la méthode décrit (recalcul indépendant : écart maximal de 5·10⁻⁷, aucune erreur factuelle trouvée dans les données). Les classements aberrants viennent de **règles méthodologiques** : des dimensions calculées sur un seul indicateur, des scores globaux sur deux dimensions, deux proxys faibles, un double comptage et une asymétrie de couverture entre pays riches et pays pauvres. Ces règles sont des choix qui t'appartiennent. Elles sont désormais dans un **registre de 12 décisions arbitrables** ; **aucune n'a été appliquée au score officiel**.

Correspondance avec les livrables demandés (noms adaptés à l'architecture du dépôt) :

| Livrable du brief | Fichier |
|---|---|
| AUDIT_REPORT.md | `AUDIT_REPORT.md` (ce fichier) |
| INDICATOR_DICTIONARY.csv | `INDICATOR_DICTIONARY.csv` (35 lignes : 19 retenus, 4 candidats, 12 exclus) |
| THEORETICAL_REFERENCES.md | `THEORETICAL_REFERENCES.md` |
| DATA_QUALITY_REPORT.csv | `DATA_QUALITY_REPORT.csv` (3 282 observations) |
| ANOMALIES.csv | `ANOMALIES.csv` (319 anomalies, 160 entités) |
| DECISION_REGISTER.csv | `DECISION_REGISTER.csv`, généré à partir de `config/decisions.json` (source de vérité) |
| METHODOLOGY.md | `docs/METHODOLOGIE.md` (régénéré) |
| ROBUSTNESS_REPORT.md | `docs/ROBUSTESSE.md` (14 tests) et `data/audit/simulations.json` |
| Tests automatisés | `tests/test_audit.py` (nouveau, 23 tests), `tests/test_html.py` (10 tests), `tests/test_engine.py` (18 tests) |
| Configuration versionnée | `config/dimensions.json` (règles de couverture), `config/indicateurs.json`, `config/decisions.json` |
| HTML autonome corrigé | `dist/socialistometre.html` |
| CHANGELOG.md | mis à jour |

Les éditions archivées `editions/v1.0` et `editions/v1.1` n'ont pas été modifiées.

---

## A. Diagnostic

| Élément | Nombre |
|---|---|
| Indicateurs examinés | 19 retenus + 2 variantes + 2 candidats nouveaux + 12 exclus = 35 |
| Proxys faibles (niveau 3) dans le score officiel | 2 : A5 (qualité de la réglementation WGI), C2 (part du privé dans le primaire) |
| Double comptage arithmétique | 1 : B6 est inclus dans B5 |
| Définition contraire à la règle écrite | 1 : D2, borne basse 0 au lieu de −4 |
| Paires fortement corrélées (ρ ≥ 0,8) | 15, dont D1–D4 entre eux, A4/A6 avec D, B5–B6 |
| Indicateurs conservés tels quels | 15 |
| Erreurs factuelles dans les données | **0** |
| Pays et territoires examinés | 237 (tous) |
| Anomalies identifiées | 319, sur 160 entités |
| Défauts de code | 6 (tous corrigés ; aucun ne modifiait le score officiel) |

**Anomalies par catégorie** (`ANOMALIES.csv`)

| Catégorie | Nombre | Nature |
|---|---|---|
| Dimension calculée sur un seul indicateur | 109 | fragilité méthodologique |
| Proxy faible C2 qui modifie le score de plus de 5 points | 49 | conceptuelle |
| Compensation entre dimensions (écart supérieur à 70 points) | 34 | constat |
| Score dominé par un seul indicateur (retrait : plus de 10 points d'écart) | 28 | fragilité méthodologique |
| Valeur écrêtée qui domine une dimension peu couverte | 25 | fragilité méthodologique |
| Score global calculé sur 2 dimensions | 23 | fragilité méthodologique |
| Prélèvements faibles avec une faible capacité fiscale (V-Dem) | 20 | conceptuelle |
| Entités qui se recouvrent (ex. Tibet et Chine, Crimée et Ukraine) | 16 | correspondance |
| Borne de D2 écrêtée | 9 | définition |
| Double comptage B5 ⊃ B6 (effet supérieur à 3 points) | 5 | mathématique |
| Cotisations obligatoires à des fonds privés non comptées (Chili) | 1 | définition / donnée manquante |

### Principales causes démontrées des évaluations aberrantes

1. **Dimensions à un seul indicateur.** 90 des 222 scores globaux contiennent au moins une dimension calculée sur un seul indicateur (A : 15, B : 40, C : 44, D : 10). Pour mesurer l'erreur, on prend les pays qui disposent de tous les indicateurs d'une dimension et on recalcule la dimension avec seulement *k* d'entre eux, sur tous les sous-ensembles possibles :

   | Dimension | k = 1 (médiane / P90) | k = 2 | k = 3 |
   |---|---|---|---|
   | A (54 pays) | 9,4 / 19,2 | 5,2 / 13,8 | 3,5 / 8,9 |
   | B (30 pays) | 12,0 / 33,0 | 7,6 / 18,9 | 4,8 / 14,3 |
   | C (53 pays) | 24,6 / 45,3 | 12,3 / 22,6 | — |
   | D (195 pays) | 7,1 / 17,2 | 4,7 / 9,1 | 2,4 / 5,7 |

   Une dimension à un indicateur peut donc s'écarter de 25 à 45 points de la valeur qu'elle aurait avec des données complètes, alors qu'elle pèse autant dans le score global.

2. **Scores globaux sur deux dimensions.** Sur les 158 pays complets, un score recalculé avec A et une seule autre dimension s'écarte du score complet de 5,4 points en médiane (P90 15,3 ; max 28,4). Avec 3 dimensions, l'écart tombe à 3,7 (P90 9,1).

3. **Asymétrie de couverture.** Les mesures de la réglementation et de la propriété publique (A2, A3, C1 de l'OCDE) n'existent que pour 56 pays. Ailleurs, l'État n'est mesuré que par des **montants** : prélèvements (B5, B6) et consommation publique (C3). Or ces montants sont corrélés à la **capacité fiscale** (V-Dem v2stfisccap : ρ = 0,64 pour B5, 0,65 pour B6) et à l'état de droit (ρ = 0,66). Résultat : B5 normalisé vaut en moyenne **91,1** dans les pays à faible revenu contre **32,5** dans les pays à revenu élevé. Une faible capacité à lever l'impôt est lue comme du libéralisme, et aucune mesure de la coercition non fiscale ne vient compenser.

4. **Écrêtage des bornes P5–P95.** Les valeurs au-delà des percentiles sont ramenées à 0 ou 100 : 7 pays ont B5 = 100, 9 ont C3 = 100, 12 ont B3 = 100. Dans une dimension à un indicateur, cet écrêtage fixe la dimension entière à 0 ou 100.

5. **Deux proxys faibles** (A5, C2) et **un double comptage** (B5 ⊃ B6), détaillés en section E.

Instabilité globale : le test existant T08 montre une largeur médiane de l'intervalle de rang P5–P95 de **64 places** sur 222. Le rang d'un pays n'est donc pas précis à mieux que ±30 places. Ce test était affiché « RÉUSSI » sans aucun critère ; il est maintenant en AVERTISSEMENT (voir section C).

---

## B. Exemples concrets (chiffres, sources, formules)

Formule de normalisation : `score = 100 × clip((x − L)/(U − L), 0, 1)`, ou `100 × clip((U − x)/(U − L), 0, 1)` pour un indicateur orienté vers le pôle socialisant. Score global = Σ w_d·S_d / Σ w_d sur les dimensions disponibles.

**Chypre du Nord, 2ᵉ mondiale (76,8).** Seules quatre observations Freedom House sont disponibles. A = A6 seul (G2 = 3 sur 4, d'où 75,0) ; D = moyenne de D2, D3, D4 = 82,2 ; B et C sont absents. Score global = (0,45 × 75 + 0,15 × 82,2) / 0,60 = **76,8**. A6 apporte à lui seul 56,3 points. Cause : règles de couverture (DEC-01, DEC-02). Certitude élevée. Avec DEC-01, l'entité n'a plus de score global.

**Îles Caïmans, 15ᵉ (70,5).** B = 100 sur le seul taux d'impôt sur les sociétés (0 %, OCDE CIT 2023) ; C = 99,3 avec C2 (48,6 % du primaire dans le privé, normalisé à 98,5) et C3 (consommation publique de 2,6 % du PIB, valeur 2020, sous la borne P5 de 6,56, donc 100) ; D = D1 seul (66,2). Trois dimensions sur quatre reposent sur un ou deux chiffres. Avec DEC-01 : 62,5 (rang 59). Dans le scénario recommandé, l'entité n'a plus de score global.

**Bangladesh, 67ᵉ (61,9).** Prélèvements de 7,5 % du PIB (B5) et 1,0 % sur le travail (B6), tous deux sous la borne P5, donc B = 100. Consommation publique de 5,7 % du PIB (sous P5), donc C = 100 sur un seul indicateur. Or A = 36,5 et D = 36,4. Les 40 points de B et C viennent de trois montants faibles. Avec DEC-01 seule : 36,5 (rang 165). Scénario recommandé : 48,9 (rang 122).

**Émirats arabes unis, 27ᵉ (67,7).** B = 100 sur le seul taux d'IS de 0 % (l'OCDE publie 0 pour 2023 et 9 % à partir de 2024) ; C2 = 82,6 % dans le privé, populations expatriées comprises (normalisé à 100). Scénario recommandé : 51,1 (rang 113).

**Liechtenstein.** C = 3,8 sur le seul C2 (3,0 % dans le privé). La dimension C du pays est donc entièrement fixée par la part de l'école privée.

**France.** B5 = 46,1 % du PIB, dont B6 = 26,8 %. Les prélèvements sur le travail sont comptés deux fois dans B (B5 et B6), et une troisième fois comme taux dans B7 (coin fiscal de 46,8 %). Avec DEC-05, la France passe de 60,9 à 61,4 : B5n (prélèvements hors travail, 19,3 % du PIB) est moins pénalisant que B5.

**Chili, 1ᵉʳ (77,7).** Coin fiscal de 7,1 % (B7, normalisé à 100) et prélèvements sur le travail de 3,5 % du PIB (B6, normalisé à 90,2). L'OCDE ne compte pas comme impôts les cotisations retraite obligatoires versées aux fonds privés (AFP), alors que Friedman critique l'épargne-retraite obligatoire (P09, chap. 11, p. 283). C2 = 63,1 % dans le privé, normalisé à 100. Aucune série OCDE de ces versements n'a été trouvée dans les flux accessibles : la limite est signalée (DEC-10) et rien n'a été estimé.

**Chine.** Droits politiques Freedom House = −2. L'échelle va de −4 à 40, mais le code utilise 0–40 alors que la méthodologie annonce des « échelles naturelles » : les valeurs −3, −2 et 0 reçoivent le même score (DEC-06, effet inférieur à 1 point).

---

## C. Corrections

### Corrections factuelles (catégorie 1) : aucune nécessaire

Contrôles effectués : doublons (0) ; plages physiques (0 rejet) ; unités (les pourcentages sont tous en %, B4 est en ratio après une division par 100 documentée, aucun mélange 20 % / 0,20) ; années (fenêtre 2019–2023 respectée, B5 en 2021 ou 2022 selon les pays, valeurs antérieures à 2021 signalées) ; empreintes SHA-256 des 19 fichiers bruts ; relecture de 114 observations dans les fichiers bruts ; vérification manuelle des 6 observations Freedom House que le test T03 ne pouvait pas rapprocher par nom (SVK D2 = 37 et D3 = 15, SYR A6 = 0, RUS D4 = 2, FSM A6 = 3, KGZ D4 = 4 : toutes conformes) ; correspondance des codes pays des nouvelles données V-Dem (176 rapprochées, 3 écartées et documentées : Palestine/Cisjordanie, Gaza, Zanzibar).

### Corrections de code (catégorie 2) : appliquées, sans effet sur le score officiel

| # | Défaut | Exemple minimal | Correction |
|---|---|---|---|
| 1 | Le JavaScript comptait une dimension de poids 0 dans le minimum de 2 dimensions, contrairement à Python | Poids A = 100 %, B = C = D = 0 : Python ne donne aucun score global (1 seule dimension), l'ancien HTML donnait à chaque pays son score A | Nouveau moteur JS identique au moteur Python, parité testée à 10⁻⁹ sur la méthode officielle et sur les 27 options du registre |
| 2 | Rangs arrondis à 10⁻⁶ en JS et à 10⁻⁹ en Python | Deux scores écartés de 5·10⁻⁷ : ex æquo en JS, distincts en Python | Arrondi unifié à 10⁻⁹ |
| 3 | Le HTML ne recalculait rien : il recopiait les scores de dimension précalculés | Impossible de simuler une règle dans le navigateur | Recalcul complet à partir des valeurs brutes |
| 4 | Le texte de la méthodologie dans le HTML était périmé (cite B1, supprimé en V1.1, et omet B5, B6, B7 parmi les bornes percentiles) | — | Texte généré à partir de la configuration |
| 5 | Le test T08 (stabilité des rangs) était toujours « RÉUSSI », sans critère | Largeur médiane de 64 places affichée « RÉUSSI » | Critère : AVERTISSEMENT si la largeur médiane dépasse 10 % des entités classées |
| 6 | Code mort dans le calcul de fiabilité (variable `conteste` affectée deux fois) | Aucun effet | Ligne supprimée |

Vérifié : avec la nouvelle architecture, sans décision approuvée, le moteur reproduit **exactement** les 222 scores, rangs, dimensions et fiabilités de V1.1 (0 écart).

### Changements méthodologiques (catégories 3 à 8) : proposés, NON appliqués

Voir la section E. Ils figurent dans `config/decisions.json` et peuvent être simulés dans l'interface (« Mon scénario », « Scénario recommandé »).

### Nouveautés techniques

- **Moteur paramétrable** (`engine/scoring.py`) : minimum d'indicateurs par dimension, minimum de dimensions, inclusion et poids interne de chaque indicateur, bornes ; **contributions** de chaque indicateur au score global (leur somme égale le score, testé) ; méthode officielle = configuration de base + décisions « approuvée ».
- **Registre des décisions** (`config/decisions.json` → `DECISION_REGISTER.csv`) et **commande d'approbation** `tools/approve.py`. Une approbation incrémente la version (1.1 → 1.2), calcule l'empreinte de la configuration et écrit la comparaison avant/après.
- **Candidats d'audit collectés** : B5n = B5 − B6 (OCDE, même année) et C4 = propriété publique de l'économie (V-Dem v2clstown, paquet officiel vdemdata 16.0, SHA-256 consigné, script `tools/collect_vdem.py`).
- **Interface** : sélecteur « Méthode officielle / Scénario recommandé / Mon scénario » ; onglet **Arbitrages** (12 décisions, options, impact chiffré mondial et phrase explicative pour le pays choisi, tableau avant/après avec la dimension et l'indicateur responsables) ; **export et import** des arbitrages en JSON ; fiche pays complétée (contributions, poids effectifs, formule avec L et U, indicateurs les plus favorables et défavorables, écart entre dimensions, anomalies, sensibilité, décisions approuvées).

---

## D. Conséquences

**Méthode officielle : aucun score ni rang ne change** (aucune décision approuvée). Les fichiers sont régénérés et l'empreinte du jeu de données passe à `1412b37d…` parce que la configuration contient désormais le registre et les candidats.

**Scénario recommandé (toutes les options recommandées, non approuvé)** : 162 scores globaux (contre 222) ; Spearman des rangs communs 0,902 ; variation absolue moyenne 5,1 points ; 79 pays varient de plus de 5 points. Il est plus robuste que la méthode officielle : au retrait d'un indicateur, le Spearman minimal est de 0,978 contre 0,960 (T13 contre T06).

| Pays | Ancien score | Nouveau | Variation | Ancien rang | Nouveau | Explication principale |
|---|---|---|---|---|---|---|
| Émirats arabes unis | 67,7 | 51,1 | −16,6 | 27 | 113 | B retirée (1 seul indicateur : B3 = 0 %) ; C 89,0 → 62,1 |
| Bénin | 47,3 | 63,1 | +15,8 | 153 | 67 | C4 ajouté (contribution 0 → 10,4) ; B retirée |
| Guinée équatoriale | 33,2 | 18,2 | −15,0 | 192 | 162 | B retirée (B5, B6 seuls) |
| Bahreïn | 65,3 | 51,7 | −13,6 | 45 | 110 | B retirée (B3 = 0 %) |
| Bangladesh | 61,9 | 48,9 | −13,0 | 67 | 122 | B retirée ; C 100 → 81,6 |
| Roumanie | 59,7 | 72,1 | +12,4 | 83 | 23 | C 49,2 → 72,9 (C4) ; B retirée |
| Irlande | 76,3 | 82,4 | +6,1 | 3 | 1 | C 58,0 → 84,4 (C4, C2 retiré) |
| Suisse | 75,1 | 81,7 | +6,6 | 5 | 2 | idem |
| Chili | 77,7 | 76,6 | −1,2 | 1 | 7 | C2 retiré (contribution 6,7 → 0) |
| États-Unis | 70,7 | 77,7 | +7,0 | 13 | 4 | C4 (3,74 sur 4) |
| France | 60,9 | 65,2 | +4,4 | 73 | 56 | C 49,3 → 64,0 ; A5 retiré |
| Chine | 44,9 | 46,6 | +1,7 | 162 | 127 | B5 → B5n ; C4 = 1,35 sur 4 |
| Russie | 31,9 | 39,3 | +7,4 | 196 | 145 | C 27,5 → 49,3 (C2 retiré : 1,3 % dans le privé → 0,3) |
| Cuba | 37,2 | 29,1 | −8,1 | 188 | 159 | B retirée (B5, B6 seuls) |

60 entités perdent leur score global dans ce scénario (elles restent affichées avec leurs scores de dimension). Ce sont surtout des micro-États, des territoires et les entités Freedom House infra-étatiques, mais aussi **Venezuela, Corée du Nord, Myanmar, Yémen, Afghanistan, Irak, Jordanie, Tunisie, Somalie, Turkménistan** : faute de données suffisantes, aucun score comparable ne peut leur être donné. C'est le prix de la comparabilité, et c'est à toi de l'arbitrer (DEC-01, DEC-02).

**Effet secondaire à connaître :** avec B ≥ 3 indicateurs, la dimension B n'existe plus que pour 91 des 162 pays classés, surtout ceux de l'OCDE. Les pays riches restent pénalisés par leurs prélèvements, alors que beaucoup d'autres n'ont plus de dimension B du tout. Avec B ≥ 2, elle existerait pour 112 pays. Les deux options sont simulables.

**Pays méthodologiquement sensibles :** 111 entités voient leur score varier de plus de 10 points selon les options du registre (étendue entre scénarios, ce n'est pas un intervalle de confiance). Cette étendue est affichée dans chaque fiche.

Le détail par pays est dans `data/audit/avant_apres_scenario_recommande.csv`, et l'impact de chaque option prise isolément dans `data/audit/simulations.json`.

---

## E. Décisions qui nécessitent ton arbitrage

Elles sont classées selon ta grille : **choix de mesure** (B) ou **choix normatif** (C). Rien n'est appliqué sans ton accord. Impact = option recommandée seule, par rapport à la méthode officielle.

| Id | Décision | Nature | Options | Recommandation de l'audit | Impact chiffré |
|---|---|---|---|---|---|
| DEC-01 | Minimum d'indicateurs par dimension | mesure (cat. 8) | 1 partout (V1.1) · A≥3, B≥3, C≥2, D≥2 · 2 partout | A≥3 B≥3 C≥2 D≥2 (critère : erreur médiane ≤ 5 points) | 199 scores ; ρ = 0,909 ; max 25,4 pts (Bangladesh −25,4, Liechtenstein +22,6) |
| DEC-02 | Minimum de dimensions pour un score global | mesure (cat. 8) | 2 (V1.1) · 3 · 4 | 3, dont A | 199 scores ; les autres inchangés |
| DEC-03 | C2 (part du privé dans le primaire), proxy faible | normatif (cat. 6) | garder · retirer · poids 0,5 | retirer (mesure la fourniture, pas le choix ni le financement, P07/P08) | ρ = 0,960 ; max 15,6 pts |
| DEC-04 | A5 (WGI qualité de la réglementation), proxy faible | normatif (cat. 6) | garder · retirer | retirer (définition circulaire) | ρ = 0,992 ; max 7,2 pts |
| DEC-05 | Double comptage B5 ⊃ B6 | mesure (cat. 3) | garder · B5n = B5 − B6 · poids 0,5 | B5n (tous les prélèvements comptés une fois, sans distinction de nature) | ρ = 0,991 ; max 13,8 pts |
| DEC-06 | Borne basse de D2 | mesure (cat. 3) | 0–40 · −4–40 | −4–40 (échelle naturelle) | max 0,7 pt |
| DEC-07 | Ajout de C4 (V-Dem, propriété publique de l'économie, 176 pays) | mesure (cat. 7) | ne pas ajouter · ajouter | ajouter (mesure directe de la propriété, distincte des dépenses et de la fourniture) | ρ = 0,991 ; max 7,3 pts |
| DEC-08 | Figer les bornes percentiles de l'édition | mesure (cat. 8) | dynamiques · figées | figer (une correction ne se propage plus aux autres pays) | 0 aujourd'hui |
| DEC-09 | Prélèvements faibles et capacité fiscale | **normatif** (cat. 6) | lecture littérale P18 + avertissement · retirer B5/B6 | lecture littérale + avertissement (fidèle à P18) | 0 (l'option « retirer » : max 16,6 pts) |
| DEC-10 | Cotisations obligatoires à des fonds privés (Chili) | fait / mesure (cat. 7) | signaler | signaler ; aucune estimation sans source | — |
| DEC-11 | A4/A6 corrélés à la dimension D (ρ 0,84–0,90) | **normatif** (cat. 6) | garder · retirer A6 | garder et documenter (P01, P15) | 0 (l'option « retirer A6 » : 208 scores, max 7,4 pts) |
| DEC-12 | Bornes théoriques 0–6 des indicateurs PMR | mesure (cat. 8) | théoriques · percentiles | théoriques (score absolu plutôt que relatif, §13 du brief) | 0 (l'option « percentiles » : max 25,2 pts) |

**Point de vigilance sur le niveau 3.** Ta règle dit qu'un indicateur de niveau 3 ne compte pas sans ton approbation explicite. J'ai classé A5 et C2 au niveau 3, mais ce classement est **mon jugement**. Je ne les ai donc pas retirés d'office : DEC-03 et DEC-04 te demandent de confirmer ce classement.

**Pour trancher :**
- dans l'explorateur, onglet « Arbitrages » : coche une option par décision, regarde l'effet, puis « Exporter mes arbitrages (JSON) » ;
- puis, dans le dépôt : `python3 tools/approve.py --import arbitrages_socialistometre_AAAA-MM-JJ.json` (ou `python3 tools/approve.py DEC-01 A3_B3_C2_D2`, `--rejeter DEC-09`, `--liste`), et relance la chaîne de calcul (en-tête de `tools/approve.py`). La version passe alors à 1.2 et une nouvelle édition est archivée sans écraser la V1.1.

---

## F. Validation

**Tests réellement exécutés le 28 octobre 2026**

| Suite | Résultat |
|---|---|
| `tests/test_engine.py` (18), `tests/test_audit.py` (23), `tests/test_html.py` (10, Chromium hors ligne) | **51 / 51 réussis** |
| Recalcul indépendant pandas/numpy (`tools/audit/recalcul_independant.py`) | 0 écart (max 5·10⁻⁷, dû à l'arrondi du fichier) |
| Parité moteur JS du navigateur / Python | écart ≤ 10⁻⁹ sur la méthode officielle, le scénario recommandé et chacune des 27 options |
| Robustesse `tools/run_robustness.py` | 14 tests ; **0 échec critique** ; 8 réussis, 4 avertissements (T05 poids, T06 retrait d'un indicateur, T07 normalisation, T08 stabilité des rangs), 2 informatifs |

Les tests de cohérence du §24 sont tous couverts : pondérations valides ; formules (cas artificiels 0 et 100, sens inversés) ; conservation des valeurs brutes ; donnée manquante jamais remplacée par zéro ; scores partiels signalés ; bornes [0, 100] ; somme des contributions égale au score global ; effet d'une modification de poids conforme à la formule ; valeur extrême (10³⁰⁰) sans erreur numérique ; déterminisme ; égalité HTML/moteur ; flux d'approbation testé dans une copie du dépôt.

Tests de robustesse ajoutés : T13 (scénario recommandé : retrait d'un indicateur, ρ min = 0,978 ; rang / z-score : 0,965 / 0,973) ; T14 (comparaison de périodes : la méthode officielle appliquée à la fenêtre 2016–2020 donne ρ = 0,971 avec l'édition 2023, pour une variation moyenne de 2,4 points).

**Ce qui n'a pas pu être fait**
- Les données des cotisations obligatoires versées à des fonds privés (OCDE « non-tax compulsory payments ») ne figurent pas dans les flux SDMX accessibles : DEC-10 reste ouvert.
- *Free to Choose* n'est toujours pas accessible : le corpus reste limité à *Capitalisme et liberté*.
- Les incertitudes publiées par V-Dem (codelow/codehigh) sont collectées mais pas encore propagées dans la fiabilité.

**Fiabilité du classement.** Aucun contrôle critique n'échoue : l'implémentation est fiable. **En revanche, je ne considère pas le classement officiel V1.1 comme fiable pour comparer des pays de couvertures différentes** : 90 scores reposent sur au moins une dimension à un indicateur, et le rang n'est précis qu'à environ ±30 places (T08). Les décisions DEC-01 à DEC-08 traitent ces causes ; leur adoption t'appartient.

---

## Distinguer les incertitudes

| Type | Où elle est mesurée |
|---|---|
| Statistique | WGI et V-Dem publient des marges d'erreur (non propagées ici) ; aucun intervalle de confiance n'est présenté |
| Liée aux données | fiabilité par pays, couverture, `DATA_QUALITY_REPORT.csv`, T09 (masquage d'un tiers des indicateurs : écart médian 3,3 points, P95 12,5) |
| Méthodologique | T05–T08, T13, étendue entre les options du registre (111 entités à plus de 10 points) |
| Choix normatifs | DEC-03, DEC-04, DEC-09, DEC-11 : à toi de trancher |

## Reproduire

```
pip install -r requirements.txt            # + pyreadr pour tools/collect_vdem.py
python3 tools/build_dataset.py && python3 engine/scoring.py && python3 tools/run_robustness.py
python3 tools/audit/diagnostic.py && python3 tools/audit/simulate.py && python3 tools/audit/make_audit_files.py
python3 tools/make_docs.py && python3 tools/build_html.py
python3 tools/audit/recalcul_independant.py
python3 -m unittest discover -s tests
```
