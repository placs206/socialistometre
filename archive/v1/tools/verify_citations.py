#!/usr/bin/env python3
"""Vérifie que chaque citation de corpus/principes.json figure littéralement sur la page indiquée.

Usage : python3 tools/verify_citations.py <pages.json produit par extract_corpus.py> [--sortie corpus/verification_citations.json]
Normalisation tolérante : espaces/sauts de ligne, apostrophes, guillemets, espaces insécables.
"""
import json, re, sys, os, unicodedata

def norm(s):
    s = unicodedata.normalize("NFKC", s).replace("’", "'").replace("«", "").replace("»", "")
    s = s.replace("­", "")
    # césures de l'extraction PDF : caractère de contrôle (ex. U+0002) suivi d'un saut de ligne
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]\s*", "", s)
    s = re.sub(r"-\s*\n\s*", "-", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s+([;:,.!?])", r"\1", s)
    return s.strip().lower()

def main():
    pages = json.load(open(sys.argv[1], encoding="utf-8"))
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pr = json.load(open(os.path.join(root, "corpus", "principes.json"), encoding="utf-8"))
    res, ok, ko = [], 0, 0
    for p in pr["principes"]:
        for r in p["refs"]:
            txt = pages["pages"].get(str(r["page"]))
            found = bool(txt) and norm(r["citation"]) in norm(txt)
            res.append({"principe": p["id"], "page": r["page"], "citation": r["citation"], "verifiee": found})
            ok += found; ko += (not found)
    out = {"source_sha256_texte": pages["source_sha256"], "edition": pages["edition"],
           "total": ok + ko, "verifiees": ok, "echecs": ko, "detail": res}
    dst = os.path.join(root, "corpus", "verification_citations.json")
    if "--sortie" in sys.argv: dst = sys.argv[sys.argv.index("--sortie") + 1]
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{ok}/{ok+ko} citations vérifiées")
    for r in res:
        if not r["verifiee"]: print("ÉCHEC", r["principe"], "p.", r["page"], "→", r["citation"])
    sys.exit(1 if ko else 0)
main()
