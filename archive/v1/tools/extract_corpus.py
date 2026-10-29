#!/usr/bin/env python3
"""Segmente le texte extrait de « Capitalisme et liberté » (Leduc.s, 2010) par page imprimée.

Usage : python3 tools/extract_corpus.py <texte_brut.txt> <sortie.json>
Le texte intégral N'EST PAS versionné dans le dépôt (droit d'auteur) : chacun doit fournir sa copie.
Convention : le numéro de page imprimé figure en fin de page ; le texte de la page N
se trouve donc entre la ligne « N-1 » (ou précédente) et la ligne « N ».
"""
import json, re, sys, hashlib

def segment(text):
    lines = text.splitlines()
    pages, buf, last = {}, [], 8
    for ln in lines:
        m = re.fullmatch(r"\s*(\d{1,3})\s*", ln)
        if m:
            n = int(m.group(1))
            if last < n <= last + 4:
                pages[n] = "\n".join(buf).strip()
                buf, last = [], n
                continue
        buf.append(ln)
    return pages

if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    raw = open(src, encoding="utf-8").read()
    pages = segment(raw)
    out = {"source_sha256": hashlib.sha256(raw.encode()).hexdigest(),
           "edition": "Milton Friedman, Capitalisme et liberté, trad. A. M. Charno, Leduc.s, 2010 (éd. orig. Capitalism and Freedom, Univ. of Chicago Press, 1962)",
           "n_pages": len(pages), "pages": {str(k): v for k, v in pages.items()}}
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False)
    print(len(pages), "pages ; de", min(pages), "à", max(pages))
