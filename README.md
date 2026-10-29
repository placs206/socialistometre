# Socialistomètre V2 — repère économique × politique

Explorateur de données qui place chaque pays ou territoire dans un repère à deux axes indépendants, **à partir des seuls scores officiels publiés par des organismes de référence** :

| Axe | Source principale (coordonnée officielle) | Source de comparaison |
|---|---|---|
| X — liberté économique | Fraser Institute, *Economic Freedom of the World* (EFW), indice synthétique | Heritage Foundation, *Index of Economic Freedom* |
| Y — libéralisme politique | V-Dem, *Liberal Democracy Index* (v2x_libdem) | Freedom House, *Freedom in the World* |

Le projet n'attribue aucune note : il importe, rattache, met à l'échelle 0-100 (transformation affine fixe et réversible) et affiche. Aucune moyenne entre sources, aucun ajustement manuel, aucune valeur estimée.

**Explorateur** : `index.html` (fichier unique, fonctionne hors ligne). Méthode : [METHODOLOGY.md](METHODOLOGY.md) · Sources et licences : [SOURCES.md](SOURCES.md) · Structure des données : [DATA_DICTIONARY.md](DATA_DICTIONARY.md) · Journal : [CHANGELOG.md](CHANGELOG.md) · Rapport de validation : [docs/RAPPORT_VALIDATION_V2.md](docs/RAPPORT_VALIDATION_V2.md) · Audit de l'ancienne grille : [docs/AUDIT_ANCIENNE_GRILLE.md](docs/AUDIT_ANCIENNE_GRILLE.md).

## État de l'édition V2.0.0 (2026-10-29)

- Fraser : édition **EFW 2025** (données 2023). L'édition EFW 2026 (données 2024) est publiée mais n'a pas pu être téléchargée depuis l'environnement de travail (protection anti-robots) : voir « Mettre à jour ».
- V-Dem : **v16** (données 2025). Freedom House : **FIW 2026** (données 2025) + historique FIW 2013-2024. Heritage : **2026** (2e sem. 2024 – 1er sem. 2025).
- Scénario officiel (Fraser × V-Dem, période la plus récente) : 162 entités à deux coordonnées, 3 avec X seul, 17 avec Y seul, 57 sans coordonnée, sur 239 entités du référentiel. Écart de 2 ans entre les périodes de X et de Y : un mode « année commune 2023 » est proposé.

## Arborescence

```
config/            sources.json (éditions, échelles, licences), parametres.json (configuration officielle), contexte.json
data/raw/<source>/ MANIFEST.json (URL, date, SHA-256) + extraction littérale CSV ; _telechargements/ non versionné
data/reference/    pays.csv (identifiants stables), correspondances.csv (source → identifiant, méthode, note)
data/processed/    observations.csv, contexte.csv, anomalies.csv, coordonnees.json
data/contestations/contestations.csv
src/               importers/ (extraction), build.py, transform.py (seule règle d'échelle), coordinates.py (seule règle de sélection)
tools/             collect.py, init_reference.py, build_html.py, template.html, compare_v1.py, validate.py, make_edition.py
tests/             test_pipeline.py, test_html.py
editions/          v1.0, v1.1 (ancienne méthode), v2.0.0
archive/v1/        code, données, documentation et HTML de l'ancien indice composite (reproductible en place)
```

## Reproduire

```
pip install -r requirements.txt && python3 -m playwright install chromium
python3 tools/validate.py AAAA-MM-JJ        # build + coordonnées + HTML + 37 tests ; code 1 si un test critique échoue
python3 tools/make_edition.py AAAA-MM-JJ    # archive editions/v<version>/ (refusé si non validé)
```

## Mettre à jour (à la demande)

1. `python3 tools/collect.py` puis `python3 -m src.extract` (re-téléchargement et ré-extraction ; les empreintes changent si les fichiers changent).
2. Nouvelle édition d'une source : la déclarer dans `config/sources.json`, adapter l'importeur si le format change, puis `python3 tools/init_reference.py` et relire les rapprochements « manuel ».
   - **EFW 2026** : télécharger le fichier officiel « master index data for researchers » (.xlsx) sur fraserinstitute.org/economic-freedom/dataset, le déposer sous `data/raw/fraser/_telechargements/efw2026.xlsx`, passer `efw2026.statut` à `importee` et `edition_officielle_v2` à `efw2026`, puis relancer.
3. Toute modification de source principale, d'indicateur, d'échelle ou de règle = nouvelle version de `config/parametres.json` et nouvelle édition.
4. `python3 tools/validate.py` puis `python3 tools/make_edition.py`.

## Attribution

Fraser Institute (EFW), The Heritage Foundation (IEF), V-Dem Institute (CC BY-SA 4.0), Freedom House (FIW), Banque mondiale et OCDE (données contextuelles). Détails dans [SOURCES.md](SOURCES.md).
