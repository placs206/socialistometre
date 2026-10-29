# Socialistomètre

Indice mondial continu du pôle socialisant (0) au pôle libéral (100), inspiré exclusivement de *Capitalisme et liberté* de Milton Friedman. **V1.2** — données 2023, 237 entités (171 avec score global ; méthode arbitrée le 2026-10-29, voir `CHANGELOG.md`).

- Explorateur autonome (hors ligne) : `dist/socialistometre.html` (ou `editions/v1.2/`)
- Méthodologie : `docs/METHODOLOGIE.md` · Rapport de validation : `docs/RAPPORT_V1.md` · Robustesse : `docs/ROBUSTESSE.md`
- Journal : `CHANGELOG.md` · Comparaison V1.0→V1.1 : `docs/COMPARAISON_V1.0_V1.1.md`
- **Audit du 2026-10-28** : `AUDIT_REPORT.md` · registre des décisions à arbitrer : `DECISION_REGISTER.csv` (source : `config/decisions.json`) · `ANOMALIES.csv` · `INDICATOR_DICTIONARY.csv` · `DATA_QUALITY_REPORT.csv` · `THEORETICAL_REFERENCES.md`

## Arbitrer une décision
Explorateur → onglet « Arbitrages » → exporter le JSON, puis `python3 tools/approve.py --import fichier.json` (ou `python3 tools/approve.py --liste`). Seules les décisions approuvées modifient la méthode officielle ; une approbation crée une nouvelle version.

## Arborescence
`data/raw` (sources brutes + MANIFEST SHA-256) · `data/processed` (observations, scores, stabilité) · `config` (dimensions, dictionnaire des indicateurs) · `corpus` (bibliographie, principes, vérification des citations) · `engine` (normalisation et calcul) · `tools` (collecte, construction, robustesse, HTML, archive) · `tests` · `editions` (éditions archivées).

## Reproduire
```
pip install -r requirements.txt
python3 tools/build_dataset.py && python3 engine/scoring.py
python3 tools/run_robustness.py
python3 tools/audit/diagnostic.py && python3 tools/audit/simulate.py && python3 tools/audit/make_audit_files.py
python3 tools/make_docs.py && python3 tools/build_html.py && python3 tools/audit/recalcul_independant.py
python3 -m unittest discover -s tests          # moteur ; tests/test_html.py : interface (Playwright)
python3 tools/make_edition.py AAAA-MM-JJ
```
`tools/collect_data.py` et `tools/collect_vdem.py` retéléchargent les sources (mise à jour sur demande uniquement). Le texte intégral du livre n'est pas versionné (droits d'auteur) ; `tools/extract_corpus.py` et `tools/verify_citations.py` permettent de re-vérifier les citations à partir d'un exemplaire.

## Avertissements
Un score n'a de sens qu'avec sa fiabilité et sa couverture. La dimension C ne repose que sur 3 indicateurs. Voir les limites dans la méthodologie.
