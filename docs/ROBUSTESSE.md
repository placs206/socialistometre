# Tests de robustesse et de validation — Socialistomètre V1.0

Généré par `python3 tools/run_robustness.py` (graine 20261028). Les tests marqués CRITIQUE bloquent la validation en cas d'échec.

| Test | Nom | Critique | Résultat | Détail |
|---|---|---|---|---|
| T01 | Recalcul mathématique indépendant (numpy) de toutes les valeurs normalisées, dimensions et scores globaux | oui | **RÉUSSI** | 3487 valeurs comparées ; écart maximal 5.00e-07 (arrondi du fichier : 1e-6) |
| T02 | Détection des doublons et incohérences (clés, identifiants, noms, années, traçabilité, erreurs du journal) | oui | **RÉUSSI** | doublons observations=0, doublons identifiants=0, observations orphelines=0, noms en double=[], erreurs de journal=0, hors fenêtre=0, sans source/URL=0 |
| T03 | Données brutes : empreintes SHA-256 du manifeste et relecture indépendante d'un échantillon (120 obs.) | oui | **RÉUSSI** | 16 fichiers bruts : 0 empreinte(s) divergente(s) ; échantillon de 120 observations relu dans les fichiers bruts : 3 écart(s) [('COD', 'D4', 3.0, 2.0), ('SYR', 'A6', 0.0, None), ('SYR', 'D4', 0.0, None)] |
| T04 | Données brutes et normalisées : plage [0,100], monotonie et sens d'orientation de chaque indicateur | oui | **RÉUSSI** | 17 indicateurs contrôlés ; problèmes : aucun |
| T05 | Analyse de sensibilité aux pondérations (±10 points par dimension, poids égaux, 2 000 tirages Dirichlet) | non | **AVERTISSEMENT** | Spearman minimal sur scénarios déterministes : 0.9719 ; Monte-Carlo : moyenne 0.9807, P5 0.9438, min 0.8440 |
| T06 | Recalcul en retirant un indicateur à la fois (17 recalculs) | non | **AVERTISSEMENT** | Spearman minimal 0.9524 (retrait de B3) ; écart de score moyen max 3.29 pts |
| T07 | Comparaison de plusieurs méthodes de normalisation (rang, z-score logistique, percentiles partout, P10-P90) | non | **RÉUSSI** | Spearman minimal par rapport à la méthode principale : 0.9401 |
| T08 | Stabilité des rangs et des scores (600 rééchantillonnages : 80 % des indicateurs + poids perturbés) | non | **RÉUSSI** | largeur médiane de l'intervalle de rang P5-P95 : 59.0 places ; P90 : 103 places ; intervalles enregistrés pour 222 entités (affichés dans l'interface) |
| T09 | Comportement en présence de données manquantes (masquage aléatoire de 1/3 des indicateurs ; règle « dimension A exigée » ; avertissements) | oui | **RÉUSSI** | masquage 1/3 sur 144 pays complets × 300 tirages : écart absolu médian 3.53 pts, P95 12.94 pts, Spearman moyen 0.8790 ; règle assouplie (A non exigée) ajouterait 5 entités à score global (Curaçao, Îles Féroé, Gibraltar, Îles Turques-et-Caïques, Îles Vierges britanniques…) ; incohérences d'avertissements : 0 |
| T10 | Variantes d'indicateurs (tarif pondéré ; scolarisation privée secondaire) et redondances intra-dimension | non | **RÉUSSI** | variantes : A1→A1alt ρ=0.9948, C2→C2alt ρ=0.9786 ; paires redondantes (/ρ/≥0,85) : {'A4~A5': {'n': 205, 'spearman': 0.883}, 'D1~D2': {'n': 195, 'spearman': 0.963}, 'D1~D3': {'n': 195, 'spearman': 0.922}, 'D1~D4': {'n': 195, 'spearman': 0.949}, 'D2~D3': {'n': 210, 'spearman': 0.925}, 'D2~D4': {'n': 210, 'spearman': 0.936}, 'D3~D4': {'n': 210, 'spearman': 0.938}} |
| T11 | Corrélations de rang entre dimensions (pays à score complet) — documentation de la relation liberté économique / liberté politique (Friedman, p. 51) | non | **INFORMATIF** | n=144 ; A-B: -0.047, A-C: -0.052, A-D: 0.744, B-C: 0.039, B-D: -0.17, C-D: -0.026 (corrélation ≠ causalité) |
| T12 | Reproductibilité d'une édition : reconstruction complète depuis data/raw (jeu de données + scores) et comparaison d'empreintes | oui | **RÉUSSI** | 5 fichiers recalculés ; divergences : aucune ; empreinte du jeu de données 0db87080a1839ec9… |

Échecs critiques : aucun
