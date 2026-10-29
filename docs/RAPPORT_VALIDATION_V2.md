# Rapport de validation — édition V2.0.0 (2026-10-29)

Statut : **VALIDÉ** — 37 tests sur 37 réussis (26 pipeline, 11 interface), aucun ignoré ; résultats test par test dans `docs/validation.json` (régénéré par `tools/validate.py`). Tests exécutés dans Chromium 153 (Playwright), contexte hors ligne.

## 1. État initial du dépôt

`placs206/socialistometre`, branche principale, commit 747fef8 (« V1.1 », 2026-10-28) : indice composite V1.1 (19 indicateurs, 4 dimensions), moteur `engine/scoring.py`, outils, 18 tests moteur + 7 tests HTML, HTML `dist/socialistometre.html`, éditions `editions/v1.0`, `v1.1`. Deux fichiers de cache Python étaient versionnés (retirés).

## 2. Causes des défauts de l'ancienne grille

Voir `docs/AUDIT_ANCIENNE_GRILLE.md` : scores globaux sur 2 à 4 indicateurs classés avec les autres (Chypre du Nord 2e, Haut-Karabagh 0,0), couverture inégale (OCDE), normalisation dépendante de l'échantillon, choix interprétatifs instables, confusion des libertés économique et politique, années hétérogènes.

## 3. Architecture et fichiers

Nouveaux : `config/sources.json`, `config/parametres.json`, `config/contexte.json` ; `data/raw/{fraser,heritage,vdem,freedomhouse,contexte}/` (manifestes + extractions) ; `data/reference/pays.csv`, `correspondances.csv` ; `data/processed/observations.csv`, `contexte.csv`, `anomalies.csv`, `coordonnees.json` ; `data/contestations/contestations.csv` ; `src/{common,transform,build,coordinates,extract}.py`, `src/importers/{fraser,heritage,vdem,freedomhouse}.py` ; `tools/{collect,init_reference,build_html,template.html,compare_v1,validate,make_edition}.py` ; `tests/test_pipeline.py`, `tests/test_html.py` ; `index.html` ; `METHODOLOGY.md`, `SOURCES.md`, `DATA_DICTIONARY.md`, `docs/AUDIT_ANCIENNE_GRILLE.md`, ce rapport, `docs/validation.json`, `docs/comparaison_v1_v2.json` ; `editions/v2.0.0/` ; `.gitignore`.
Modifiés : `README.md` (réécrit), `CHANGELOG.md` (entrée V2.0.0), `requirements.txt`.
Déplacés sans modification dans `archive/v1/` : `config/`, `corpus/`, `engine/`, `tools/`, `tests/`, `docs/`, `data/`, `dist/`, ancien README.

## 4. Sources et éditions intégrées

| Source | Édition | Période mesurée | Entités | Statut |
|---|---|---|---|---|
| Fraser EFW | 2025 Annual Report | 2023 | 165 | importée (PDF officiel) |
| Fraser EFW | 2026 Annual Report | 2024 | — | **non importée** (fichiers bloqués par protection anti-robots) |
| V-Dem | v16 | 2000-2025 conservés | 179 en 2025 | importée (paquet officiel vdemdata) |
| Heritage IEF | 2026 | 2e sem. 2024 – 1er sem. 2025 | 184 (176 classées) | importée (PDF officiel) |
| Freedom House FIW | 2026 | 2025 | 208 | importée (tableau officiel) |
| Freedom House FIW | 2013-2024 | 2012-2023 | 209-210/an | importée (tableur officiel) |
| Freedom House FIW | 2025 | 2024 | — | non importée (aucun fichier trouvé) |

## 5. Couverture géographique

239 entités dans le référentiel (pays, territoires dépendants, entités partiellement reconnues ou contestées). 947 correspondances explicites : 175 par code V-Dem identique, 695 par nom identique, 77 manuelles (à revérifier à chaque édition).

## 6. Transformation des échelles

Fraser × 10, V-Dem × 100, Heritage et FH total identité, FH PR × 2,5 et CL × 100/60 ; exactes et réversibles (testé sur les 34 682 observations) ; ordre conservé à l'intérieur de chaque source et année (testé) ; aucune troncature (84 valeurs Freedom House hors échelle nominale, toutes années et composantes confondues, conservées et signalées dans `anomalies.csv`).

## 7-8. Coordonnées — scénario officiel (Fraser × V-Dem, plus récent)

- **Deux coordonnées : 162 entités.**
- **Une seule coordonnée : 20** — X seul : Bahamas, Belize, Brunei ; Y seul : Afghanistan, Cuba, Érythrée, Guinée équatoriale, Maldives, Corée du Nord, Îles Salomon, Soudan du Sud, Sao Tomé-et-Principe, Turkménistan, Ouzbékistan, Vanuatu, Bande de Gaza, Somaliland, Cisjordanie, Zanzibar, Kosovo.
- Aucune coordonnée : 57 (micro-États et territoires surtout).
- Écart de période X/Y : 2,0 ans pour les 162 points. Mode « année commune 2023 » : 162 points, écart 0.
- Scénarios de comparaison : Heritage × V-Dem 166 ; Fraser × Freedom House 165 ; Heritage × Freedom House 176.

## 9. Tests

| Groupe | Tests | Résultat |
|---|---|---|
| Import et extraction (effectifs, cohérence interne Fraser/Heritage/FH, ré-extraction identique depuis les fichiers officiels, empreintes des manifestes) | 6 | réussis |
| Correspondance géographique (rattachement complet, unicité, cas sensibles) | 3 | réussis |
| Données (doublons, échelles officielles, transformation exacte et réversible, conservation de l'ordre et des valeurs sources, traçabilité, années et périodes) | 7 | réussis |
| Coordonnées (aucune valeur inventée, absence ≠ zéro, règles de période, reproductibilité et fichier à jour, indépendance à l'ordre des lignes, données brutes intactes, pas de moyenne, contexte sans effet, scénario officiel unique, divergences) | 10 | réussis |
| Interface (hors ligne sans requête ni erreur, parité graphique/données/fiche, mode comparaison distinct et données intactes, absence affichée « — », période commune, onglets, zoom, contestation, mobile 390 px) | 11 | réussis |

Non testé automatiquement : Safari (macOS, iOS), Firefox, Android réel. Le HTML n'utilise que des API standard (SVG, pointer events, localStorage protégé) ; compatibilité à confirmer sur ces navigateurs.

## 10. Limites et divergences

- Fraser n'est pas à jour (édition 2025, données 2023) tant que l'EFW 2026 n'est pas importée ; le mode officiel juxtapose 2023 (X) et 2025 (Y).
- Économie : 158 entités ont Fraser et Heritage ; 3 divergences ≥ 15 points (Bolivie +18,1, Ouganda +16,3, Jordanie +15,3 ; différence médiane +4,7, périodes différentes).
- Politique : 178 entités ont V-Dem et Freedom House ; 97 divergences ≥ 15 points, différence médiane −15,8 : Freedom House est systématiquement plus élevé, notamment pour des démocraties électorales jugées dégradées par V-Dem (Mongolie −41,6, Guyana −41,2, Slovénie −38,1, Roumanie −36,6, Inde −36,0). Écart de construction (LDI multiplicatif) autant que de jugement ; le seuil de 15 points signale donc surtout ce décalage de niveau.
- Les indices reposent sur des évaluations d'experts et des pondérations propres à chaque organisme ; leurs biais éventuels sont transmis tels quels.
- Extraction depuis des PDF : contrôlée par des tests de cohérence interne et une ré-extraction identique, mais un fichier tabulaire officiel resterait préférable.
- V-Dem obtenu via le paquet officiel `vdemdata` plutôt que le téléchargement du site (formulaire nominatif).

## 11. Restant à faire

1. Importer l'EFW 2026 (fichier officiel à déposer par l'utilisateur ou accès réseau autorisé) puis nouvelle édition.
2. Importer FIW 2025 si un fichier officiel est trouvé (année 2024).
3. Tester l'interface sur Safari/iOS, Firefox et Android.
4. Éventuellement : séries historiques Fraser (fichier pour chercheurs) pour un vrai mode historique sur l'axe X.

## 12. Mise à jour

Voir README, section « Mettre à jour » : `tools/collect.py` → `python3 -m src.extract` → (nouvelle édition : `config/sources.json`, `tools/init_reference.py`) → `tools/validate.py` → `tools/make_edition.py`.
