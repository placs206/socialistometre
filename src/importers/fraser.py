"""Extraction littérale des scores officiels EFW (Fraser Institute).

Deux formats sont pris en charge :
1. EFW 2025 — rapport PDF officiel : figures 1.1a-b (indice synthétique 2023 et rang) et tableau 1.2 (notes et rangs
   des 5 domaines 2023). Extraction par coordonnées des mots (pdftotext -bbox, Poppler) puis contrôle croisé.
2. Fichier « master index data for researchers » (.xlsx) d'une édition ultérieure (EFW 2026…) déposé manuellement :
   colonnes ISO_Code / Countries / Year / Economic Freedom Summary Index / Area 1..5 (lecture par libellé de colonne,
   jamais par position supposée).

Aucune valeur n'est recalculée : l'indice synthétique est lu tel que publié. La moyenne des 5 domaines n'est calculée
que comme CONTRÔLE de cohérence de l'extraction (méthodologie officielle : moyenne simple des domaines).
"""
import os
import re
import subprocess

from src.common import DL, RAW, write_csv

FIELDS = ["edition", "nom_source", "iso_source", "annee", "summary", "rang", "area1", "rang1", "area2", "rang2", "area3",
          "rang3", "area4", "rang4", "area5", "rang5", "origine"]
NUM = re.compile(r"^-?\d+\.\d\d$")


def _words(pdf, first, last):
    out = subprocess.run(["pdftotext", "-f", str(first), "-l", str(last), "-bbox", pdf, "-"], capture_output=True, check=True,
                         text=True).stdout
    pages = out.split("<page ")[1:]
    res = []
    for pg in pages:
        ws = re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]+)</word>', pg)
        res.append([(float(a), float(b), float(c), float(d), _unesc(e)) for a, b, c, d, e in ws])
    return res


def _unesc(s):
    return s.replace("&amp;", "&").replace("&apos;", "'").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")


def _layout_text(pdf):
    return subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, check=True, text=True).stdout


def summary_from_figures(pdf, pages):
    """Figures 1.1a et 1.1b : deux colonnes « rang  pays  note » par page. Appariement par la hauteur (y)."""
    import collections
    rows = []
    for ws in _words(pdf, pages[0], pages[1]):
        # colonnes détectées sur la page : 2 colonnes de notes (x le plus fréquent des nombres « d.dd ») et 2 colonnes de rangs
        vx = sorted(x for x, n in collections.Counter(round(w[0]) for w in ws if NUM.match(w[4])).most_common(2))
        rx = sorted(x for x, n in collections.Counter(round(w[0]) for w in ws if w[4].isdigit()).most_common(2))
        assert len(vx) == 2 and len(rx) == 2 and rx[0] < vx[0] < rx[1] < vx[1], (vx, rx)
        for col_rank_x, col_val_x in zip(rx, vx):
            vals = [w for w in ws if abs(w[0] - col_val_x) < 3 and NUM.match(w[4])]
            names = sorted([w for w in ws if col_rank_x + 8 < w[0] < col_val_x - 5 and not w[4].isdigit()
                            and not NUM.match(w[4]) and w[1] > 60], key=lambda w: (w[1], w[0]))
            lines = []  # mots d'un même nom de pays : même hauteur (±1,5 pt)
            for w in names:
                if lines and abs(lines[-1][0][1] - w[1]) < 1.5:
                    lines[-1].append(w)
                else:
                    lines.append([w])
            used = set()
            for ln in lines:
                y = ln[0][1]
                rk = [w for w in ws if abs(w[0] - col_rank_x) < 3 and w[4].isdigit() and abs(w[1] - y) < 1.5]
                cand = sorted([v for v in vals if -1.5 <= v[1] - y <= 5 and id(v) not in used], key=lambda v: abs(v[1] - y))
                if not cand:
                    continue  # texte hors tableau (titres)
                if len(rk) != 1:
                    raise AssertionError(f"rang absent ou ambigu pour {' '.join(w[4] for w in ln)} : {rk}")
                used.add(id(cand[0]))
                rows.append({"rang": int(rk[0][4]), "nom": " ".join(w[4] for w in sorted(ln)), "summary": cand[0][4]})
            if len(used) != len(vals):
                raise AssertionError(f"{len(vals) - len(used)} note(s) non rattachée(s) à un pays")
    return rows


def areas_from_table(text):
    """Tableau 1.2 : « pays  note1 rang1 … note5 rang5 »."""
    pat = re.compile(r"^\s*([^\d\s][^\d]*?)\s+" + r"\s+".join([r"(-?\d+\.\d\d)\s+(\d+)"] * 5) + r"\s*$")
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.startswith("Table 1.2:"))
    out = []
    for l in lines[start:]:
        if l.startswith("Table 1.3") or "Chapter 2" in l:
            break
        m = pat.match(l)
        if m:
            g = m.groups()
            out.append({"nom": g[0].strip(), **{f"area{k + 1}": g[1 + 2 * k] for k in range(5)},
                        **{f"rang{k + 1}": g[2 + 2 * k] for k in range(5)}})
    return out


def extract_efw2025():
    pdf = os.path.join(RAW, "fraser", DL, "efw2025.pdf")
    text = _layout_text(pdf)
    assert "Economic Freedom of the World in 2023" in text, "en-tête du chapitre 1 introuvable"
    summ = summary_from_figures(pdf, (15, 16))
    key = lambda n: n.replace("\u2019", "'")  # apostrophe typographique (tableau) / droite (figures)
    areas = {key(a["nom"]): a for a in areas_from_table(text)}
    s_by = {}
    for s in summ:
        assert key(s["nom"]) not in s_by, f"doublon dans les figures : {s['nom']}"
        s_by[key(s["nom"])] = s
    noms = sorted(set(s_by) | set(areas))
    rows, problems = [], []
    for n in noms:
        s, a = s_by.get(n), areas.get(n)
        if not s or not a:
            problems.append(n)
            continue
        rows.append({"edition": "efw2025", "nom_source": a["nom"], "iso_source": "", "annee": 2023, "summary": s["summary"],
                     "rang": s["rang"], **{k: a[k] for k in a if k != "nom"}, "origine": "PDF p.15-16 (fig. 1.1a-b) ; p.17-21 (tab. 1.2)"})
    if problems:
        raise AssertionError(f"pays présents dans une seule des deux tables : {problems}")
    return rows


def extract_xlsx(path, edition):
    """Fichier officiel pour chercheurs (format Fraser). Lecture par libellés exacts ; échec explicite sinon."""
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        for hi, r in enumerate(rows[:10]):
            labels = [str(c).strip() if c is not None else "" for c in r]
            if "Economic Freedom Summary Index" in labels and "Year" in labels:
                ix = {lab: labels.index(lab) for lab in labels if lab}
                need = {"area1": "Area 1", "area2": "Area 2", "area3": "Area 3", "area4": "Area 4", "area5": "Area 5"}
                cols = {}
                for k, pref in need.items():
                    c = [lab for lab in ix if lab.startswith(pref) and "Rank" not in lab and "Data" not in lab]
                    if len(c) != 1:
                        raise AssertionError(f"colonne {pref} ambiguë ou absente : {c}")
                    cols[k] = ix[c[0]]
                out = []
                for r in rows[hi + 1:]:
                    if r[ix["Year"]] is None or r[ix["Economic Freedom Summary Index"]] in (None, ""):
                        continue
                    out.append({"edition": edition, "nom_source": r[ix["Countries"]], "iso_source": r[ix.get("ISO Code", ix.get("ISO_Code", ix.get("ISO code")))],
                                "annee": int(r[ix["Year"]]), "summary": r[ix["Economic Freedom Summary Index"]],
                                "rang": r[ix["Rank"]] if "Rank" in ix else "", **{k: r[c] for k, c in cols.items()},
                                "origine": f"{os.path.basename(path)} / {ws.title}"})
                return out
    raise AssertionError("en-têtes officiels EFW introuvables dans le classeur")


def run():
    rows = extract_efw2025()
    write_csv(os.path.join(RAW, "fraser", "efw2025_extraction.csv"), rows, FIELDS)
    x = os.path.join(RAW, "fraser", DL, "efw2026.xlsx")
    if os.path.exists(x):
        write_csv(os.path.join(RAW, "fraser", "efw2026_extraction.csv"), extract_xlsx(x, "efw2026"), FIELDS)
    return rows
