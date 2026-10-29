"""Utilitaires communs (chemins, lecture/écriture CSV-JSON, empreintes).

Aucune règle de calcul ici : les transformations d'échelle sont dans src/transform.py,
la sélection des coordonnées dans src/coordinates.py.
"""
import csv
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
REF = os.path.join(ROOT, "data", "reference")
PROC = os.path.join(ROOT, "data", "processed")
CFG = os.path.join(ROOT, "config")
DL = "_telechargements"  # sous-dossier non versionné des fichiers sources non redistribuables


def p(*parts):
    return os.path.join(ROOT, *parts)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n", extrasaction="raise")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fields})


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj, compact=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if compact:
            json.dump(obj, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        else:
            json.dump(obj, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def manifest(src):
    path = os.path.join(RAW, src, "MANIFEST.json")
    return read_json(path) if os.path.exists(path) else {"source": src, "fichiers": {}}


def save_manifest(src, man):
    write_json(os.path.join(RAW, src, "MANIFEST.json"), man)


def config(name):
    return read_json(os.path.join(CFG, name))
