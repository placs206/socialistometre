# Archive de l'ancienne méthode (indice composite V1.0 / V1.1)

Retirée de l'interface principale le 2026-10-29 (V2.0.0), conservée pour la traçabilité. Arborescence identique à celle du dépôt V1.1 (commit 747fef8) : `config/`, `corpus/`, `engine/`, `tools/`, `tests/`, `docs/`, `data/`, `dist/`. Documentation d'origine : `README_V1.md`, `CHANGELOG_V1.md`, `docs/METHODOLOGIE.md`.

Reproduction en place (les scripts calculent leurs chemins depuis leur propre dossier) :

    cd archive/v1 && pip install -r requirements_v1.txt
    python3 -m unittest tests.test_engine

Les scores V1 ne sont pas comparables aux coordonnées V2 (voir `docs/AUDIT_ANCIENNE_GRILLE.md` à la racine).
