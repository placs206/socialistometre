# Rapport de validation — Socialistomètre V1.0 (28 octobre 2026)

## 1. Principes de Friedman retenus et références vérifiées
Corpus unique : *Capitalisme et liberté* (Leduc.s 2010, pagination imprimée). 17 principes (P01–P17), 30 citations littérales, **30/30 vérifiées** automatiquement page par page (`corpus/verification_citations.json`, `tools/verify_citations.py`). *Free to Choose* n'a pas été utilisé : texte non accessible, donc non vérifiable. P16 (règle monétaire) et P17 (changes flottants) sont documentés mais non mesurés.

## 2. Dictionnaire des indicateurs admis et exclus
17 indicateurs admis : A=6, B=4, C=3, D=4 ; exclus documentés (inflation, change, Gini, subventions/transferts, prélèvements/PIB, Doing Business, Heritage/Fraser, etc.). Voir `docs/METHODOLOGIE.md` et `config/indicateurs.json`.
**Écart à la cible 5–10 par dimension : B (4) et C (3).** Aucun indicateur n'a été ajouté pour compléter la liste.

## 3. Justification des familles
A : droits de douane, barrières réglementaires aux services professionnels et prix, État de droit et qualité réglementaire (WGI), droits de propriété. B : proxy de cotisations, taux supérieur d'IR, IS, salaire minimum relatif. C : propriété publique, scolarisation privée (distinction financement/fourniture, p. 156), consommation publique. D : parole, droits politiques, libertés civiles, WGI voix. Les chevauchements conceptuels sont documentés indicateur par indicateur.

## 4. Couverture et qualité des données
237 entités ; 222 avec score global : 144 complets, 78 partiels, 11 insuffisants, 4 sans donnée. Couverture par indicateur : de 33 (B4) à 210 (A6, D2–D4). 2 462 observations ; 10 anomalies journalisées (9 valeurs extrêmes signalées, 1 chevauchement CHI/GGY/JEY). Sources brutes archivées avec SHA-256 (`data/raw/MANIFEST.json`).

## 5. Normalisation et formules
Voir `docs/METHODOLOGIE.md` §Calcul.

## 6. Résultats des tests
12 tests de robustesse (`docs/ROBUSTESSE.md`) : aucun échec critique ; 2 avertissements (T05, T06). 18 tests unitaires du moteur et 7 tests de l'interface réussis (hors ligne, zéro requête externe, parité JS/Python < 1e-5, syntaxe ES2017, mobile 375 px sans débordement). Compatibilité : tests réels sous Chromium uniquement ; Firefox/Safari/iOS non testés (code ES2017 standard, sans dépendance).
Limite du test T03 : la relecture croisée de Freedom House rapproche les pays par nom ; 3 écarts sur 120 (COD, SYR) viennent de ce rapprochement et non des données ; non investigué plus avant.

## 7. Analyse de sensibilité
Poids ±10 points : Spearman ≥ 0,972 ; 2 000 tirages : moyenne 0,981, P5 0,944, min 0,844. Retrait d'un indicateur : Spearman min 0,952 (B3). Autres normalisations : 0,940 (rang) à 0,990 (P10–P90). Stabilité des rangs : intervalle P5–P95 médian de 59 places, P90 de 103 places — **les rangs individuels sont peu précis, seuls les groupes de scores sont robustes.** Masquer 1/3 des indicateurs d'un pays complet décale son score de 3,5 points (médiane) et 12,9 (P95).

## 8. Limites et risques de biais
- B et C pauvres en indicateurs ; couverture OCDE partielle (A2, A3, B2, B4, C1) : la composition des dimensions varie selon les pays.
- B1 avantage les pays finançant la protection sociale par l'impôt général (Danemark 2e au classement global).
- Les scores partiels (A+D seulement) peuvent atteindre des rangs élevés (Chypre du Nord, 1er rang global ; voir `rang_complets`) : à lire avec la couverture.
- D très corrélée en interne (ρ 0,92–0,96) et à A (0,74) : relation liberté économique/politique documentée, non présumée.
- Freedom House (ONG) et WGI (perceptions) : sources de moindre poids.
- Friedman n'est pas la source des seuils de normalisation ; ils sont des choix du projet.
- Corrélation ≠ causalité ; aucune étiquette politique attribuée.

## 9. Instructions de reproduction
Voir `README.md`. Empreinte du jeu de données : voir `editions/v1.0/MANIFEST.json`. Reconstruction vérifiée identique (T12).

## 10. Fichiers produits
`README.md`, `CHANGELOG.md`, `requirements.txt`, `config/*`, `corpus/*`, `data/raw/*`, `data/processed/*`, `engine/scoring.py`, `tools/*`, `tests/*`, `docs/*`, `dist/socialistometre.html`, `editions/v1.0/*`.

## Décisions prises en autonomie
1. Propriétaire du dépôt : `placs206`. 2. Seul *Capitalisme et liberté* est utilisé. 3. WGI et Freedom House admis comme indicateurs (source moins pondérée). 4. Bornes fixes pour les échelles naturelles, percentiles P5–P95 sinon. 5. Règle « dimension A exigée + ≥2 dimensions » pour le score global. 6. B et C sous la cible de 5 indicateurs. 7. Doing Business et indices dérivés d'idéologie exclus. 8. Taïwan, Kosovo et 14 territoires de Freedom House inclus avec identifiants `X-…` ; chevauchement CHI/GGY/JEY signalé.
