# Socialistomètre

Indice mondial continu du pôle socialisant (0) au pôle libéral (100), inspiré exclusivement de *Capitalisme et liberté* de Milton Friedman. **V1.1** — données 2023, 237 entités (222 avec score global).

- Explorateur autonome (hors ligne) : `dist/socialistometre.html` (ou `editions/v1.1/`)
- Méthodologie : `docs/METHODOLOGIE.md` · Rapport de validation : `docs/RAPPORT_V1.md` · Robustesse : `docs/ROBUSTESSE.md`
- Journal : `CHANGELOG.md` · Comparaison V1.0→V1.1 : `docs/COMPARAISON_V1.0_V1.1.md`

## Arborescence
`data/raw` (sources brutes + MANIFEST SHA-256) · `data/processed` (observations, scores, stabilité) · `config` (dimensions, dictionnaire des indicateurs) · `corpus` (bibliographie, principes, vérification des citations) · `engine` (normalisation et calcul) · `tools` (collecte, construction, robustesse, HTML, archive) · `tests` · `editions` (éditions archivées).

## Reproduire
```
pip install -r requirements.txt
python3 tools/build_dataset.py && python3 engine/scoring.py
python3 tools/run_robustness.py && python3 tools/make_docs.py && python3 tools/build_html.py
python3 -m unittest discover -s tests          # moteur ; tests/test_html.py : interface (Playwright)
python3 tools/make_edition.py AAAA-MM-JJ
```
`tools/collect_data.py` retélécharge les sources (mise à jour sur demande uniquement). Le texte intégral du livre n'est pas versionné (droits d'auteur) ; `tools/extract_corpus.py` et `tools/verify_citations.py` permettent de re-vérifier les citations à partir d'un exemplaire.

## Avertissements
Un score n'a de sens qu'avec sa fiabilité et sa couverture. La dimension C ne repose que sur 3 indicateurs. Voir les limites dans la méthodologie.
