# Rapport de validation — Socialistomètre V1.1 (28 octobre 2026)

> V1.1 remplace V1.0 : demande de traiter impôts, taxes et cotisations comme des prélèvements, sans distinction (B1 retiré ; B5, B6, B7 ajoutés). Comparaison : `docs/COMPARAISON_V1.0_V1.1.md`. La V1.0 reste archivée dans `editions/v1.0/`.

## 1. Principes de Friedman retenus et références vérifiées
Corpus unique : *Capitalisme et liberté* (Leduc.s 2010, pagination imprimée). 20 principes (P01–P20), 34 citations littérales, **34/34 vérifiées** automatiquement page par page (`corpus/verification_citations.json`, `tools/verify_citations.py`). *Free to Choose* n'a pas été utilisé : texte non accessible, donc non vérifiable. P16 (règle monétaire) et P17 (changes flottants) sont documentés mais non mesurés.

## 2. Dictionnaire des indicateurs admis et exclus
19 indicateurs admis : A=6, B=6, C=3, D=4 ; exclus documentés (inflation, change, Gini, subventions/transferts, prélèvements/PIB, Doing Business, Heritage/Fraser, etc.). Voir `docs/METHODOLOGIE.md` et `config/indicateurs.json`.
**Écart à la cible 5–10 par dimension : C (3).** Aucun indicateur n'a été ajouté pour compléter la liste. B compte 6 indicateurs dont 3 de prélèvements (B5, B6, B7) liés entre eux (ρ B5~B6 = 0,89).

## 3. Justification des familles
A : droits de douane, barrières réglementaires aux services professionnels et prix, État de droit et qualité réglementaire (WGI), droits de propriété. B : prélèvements totaux (impôts, taxes et cotisations confondus), prélèvements sur le travail en % du PIB, coin fiscal sur le travail, taux supérieur d'IR, taux d'IS, salaire minimum relatif. C : propriété publique, scolarisation privée (distinction financement/fourniture, p. 156), consommation publique. D : parole, droits politiques, libertés civiles, WGI voix. Les chevauchements conceptuels sont documentés indicateur par indicateur.

## 4. Couverture et qualité des données
237 entités ; 222 avec score global : 158 complets, 64 partiels, 11 insuffisants, 4 sans donnée. Couverture par indicateur : de 33 (B4) à 210 (A6, D2–D4) ; B5 129, B6 115, B7 38. 2 654 observations ; 10 anomalies journalisées (9 valeurs extrêmes signalées, 1 chevauchement CHI/GGY/JEY). Sources brutes archivées avec SHA-256 (`data/raw/MANIFEST.json` ; le fichier Global Revenue Statistics, 28 Mo, est filtré à la collecte, empreinte du fichier complet conservée).

## 5. Normalisation et formules
Voir `docs/METHODOLOGIE.md` §Calcul.

## 6. Résultats des tests
12 tests de robustesse (`docs/ROBUSTESSE.md`) : aucun échec critique ; 3 avertissements (T05, T06, T07). 18 tests unitaires du moteur et 7 tests de l'interface réussis (hors ligne, zéro requête externe, parité JS/Python < 1e-5, syntaxe ES2017, mobile 375 px sans débordement). Compatibilité : tests réels sous Chromium uniquement ; Firefox/Safari/iOS non testés (code ES2017 standard, sans dépendance).
T03 : relecture indépendante de 114 observations, 0 écart ; 6 observations Freedom House de l'échantillon n'ont pas pu être rapprochées par nom exact et ne sont donc pas vérifiées par ce test.

## 7. Analyse de sensibilité
Poids ±10 points : Spearman ≥ 0,961 ; 2 000 tirages : moyenne 0,976, P5 0,929, min 0,808. Retrait d'un indicateur : Spearman min 0,960 (B3). Normalisations alternatives : Spearman minimal 0,926. Stabilité des rangs : intervalle P5–P95 médian de 64 places, P90 de 110 places — **les rangs individuels sont peu précis, seuls les groupes de scores sont robustes.** Masquer 1/3 des indicateurs d'un pays complet décale son score de 3,3 points (médiane) et 12,5 (P95).

## 8. Limites et risques de biais
- C pauvre en indicateurs ; couverture OCDE partielle (A2, A3, B2, B4, B7, C1) : la composition des dimensions varie selon les pays.
- Les prélèvements (B5–B7) mesurent le financement sans distinguer impôts, taxes et cotisations (décision V1.1) ; un faible prélèvement peut refléter une faible capacité de l'État plutôt qu'un choix libéral, et ces indicateurs ne disent rien de l'usage des fonds ni des déficits. Effet du changement : Danemark 2e → 14e rang (Spearman V1.0/V1.1 = 0,957).
- A et B sont désormais corrélées négativement (ρ = −0,47 sur les scores complets) : les pays les plus ouverts et réglementairement libéraux sont aussi, en moyenne, les plus prélevés.
- Les scores partiels (A+D seulement) peuvent atteindre des rangs élevés (voir `rang_complets` pour le rang parmi les scores complets) : à lire avec la couverture.
- D très corrélée en interne (ρ 0,92–0,96) et à A (0,74) : relation liberté économique/politique documentée, non présumée.
- Freedom House (ONG) et WGI (perceptions) : sources de moindre poids.
- Friedman n'est pas la source des seuils de normalisation ; ils sont des choix du projet.
- Corrélation ≠ causalité ; aucune étiquette politique attribuée.

## 9. Instructions de reproduction
Voir `README.md`. Empreinte du jeu de données : voir `editions/v1.0/MANIFEST.json`. Reconstruction vérifiée identique (T12).

## 10. Fichiers produits
`README.md`, `CHANGELOG.md`, `requirements.txt`, `config/*`, `corpus/*`, `data/raw/*`, `data/processed/*`, `engine/scoring.py`, `tools/*`, `tests/*`, `docs/*`, `dist/socialistometre.html`, `editions/v1.0/*` (archive de la V1.0), `editions/v1.1/*`, `docs/COMPARAISON_V1.0_V1.1.md`.

## Décisions prises en autonomie
1. Propriétaire du dépôt : `placs206`. 2. Seul *Capitalisme et liberté* est utilisé. 3. WGI et Freedom House admis comme indicateurs (source moins pondérée). 4. Bornes fixes pour les échelles naturelles, percentiles P5–P95 sinon. 5. Règle « dimension A exigée + ≥2 dimensions » pour le score global. 6. B et C sous la cible de 5 indicateurs. 7. Doing Business et indices dérivés d'idéologie exclus. 8. V1.1 : B1 retiré et remplacé par B5–B7, versionné (méthodologie 1.1) ; pondérations inchangées. 9. Taïwan, Kosovo et 14 territoires de Freedom House inclus avec identifiants `X-…` ; chevauchement CHI/GGY/JEY signalé.
