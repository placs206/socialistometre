"""Extraction littérale du tableau « 2026 Index of Economic Freedom World Rankings » (Heritage Foundation, PDF officiel).

Ordre des 12 colonnes de composantes vérifié par les coordonnées des en-têtes pivotés de la page 19 du PDF
(Property Rights, Judicial Effectiveness, Gov't Integrity, Tax Burden, Gov't Spending, Fiscal Health, Business Freedom,
Labor Freedom, Monetary Freedom, Trade Freedom, Investment Freedom, Financial Freedom) : voir check_header().
Les entités notées « N/A » (non classées) sont conservées avec leurs composantes publiées et un score global absent.
"""
import os
import re
import subprocess

from src.common import DL, RAW, write_csv

COMP = ["property_rights", "judicial_effectiveness", "government_integrity", "tax_burden", "government_spending",
        "fiscal_health", "business_freedom", "labor_freedom", "monetary_freedom", "trade_freedom", "investment_freedom",
        "financial_freedom"]
HEADER = ["Property Rights", "Judicial Effectiveness", "Gov't Integrity", "Tax Burden", "Gov't Spending", "Fiscal Health",
          "Business Freedom", "Labor Freedom", "Monetary Freedom", "Trade Freedom", "Investment Freedom", "Financial Freedom"]
FIELDS = ["edition", "nom_source", "rang_mondial", "rang_regional", "score", "variation"] + COMP + ["origine"]
V = r"(?:-?\d+(?:\.\d+)?|N/A)"
ROW_SANS_NOM = re.compile(r"^\s*(\d+|N/A)\s+(\d+|N/A)\s+(" + V + r"(?:\s+" + V + r"){13})\s*$")  # nom sur 2 lignes
ROW = re.compile(r"^\s*(\d+|N/A)\s+(\d+|N/A)\s+(\S.*?\S)\s+(" + V + r"(?:\s+" + V + r"){13})\s*$")


def pdf_path():
    return os.path.join(RAW, "heritage", DL, "ief2026.pdf")


def check_header(page=19):
    """Vérifie l'ordre des en-têtes pivotés par leur abscisse (et non par hypothèse)."""
    out = subprocess.run(["pdftotext", "-f", str(page), "-l", str(page), "-bbox", pdf_path(), "-"], capture_output=True,
                         text=True, check=True).stdout.replace("&apos;", "'").replace("’", "'")
    ws = [(float(a), float(b), e) for a, b, e in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">([^<]+)</word>', out)]
    head = [w for w in ws if w[1] < 175 and w[0] > 250]
    cols = {}
    for x, y, t in head:
        k = round(x / 6)  # mots d'une même colonne pivotée : même abscisse
        cols.setdefault(k, []).append((y, t))
    labels = []
    for k in sorted(cols):
        words = [t for y, t in sorted(cols[k], key=lambda z: -z[0]) if not re.match(r"^[\d.]+$", t) and t not in ("RANKINGS", "WORLD", "FREEDOM")]
        lab = " ".join(words).replace("Eff ectiveness", "Effectiveness")
        if lab:
            labels.append(lab)
    assert labels == HEADER, labels
    return labels


def extract():
    check_header()
    text = subprocess.run(["pdftotext", "-layout", pdf_path(), "-"], capture_output=True, text=True, check=True).stdout
    pages = text.split("\f")
    rows, seen = [], set()
    for pi, pg in enumerate(pages, start=1):
        if "WORLD RANKINGS" not in pg.upper() or pi > 40:
            continue
        lines = pg.split("\n")
        for i, line in enumerate(lines):
            m = ROW.match(line)
            m2 = None if m else ROW_SANS_NOM.match(line)
            if m:
                wr, rr, name, rest = m.groups()
            elif m2:  # nom long imprimé sur la ligne précédente et la suivante (ex. « Saint Vincent and / the Grenadines »)
                wr, rr, rest = m2.groups()
                name = (lines[i - 1].strip() + " " + lines[i + 1].strip()).strip()
                assert re.match(r"^[^\d]+$", name), (line, name)
            else:
                continue
            vals = rest.split()
            assert len(vals) == 14, line
            if name in seen:
                raise AssertionError(f"doublon {name}")
            seen.add(name)
            rows.append({"edition": "ief2026", "nom_source": name, "rang_mondial": wr, "rang_regional": rr, "score": vals[0],
                         "variation": vals[1], **dict(zip(COMP, vals[2:])), "origine": f"PDF p.{pi} (World Rankings)"})
    return rows


def run():
    rows = extract()
    write_csv(os.path.join(RAW, "heritage", "ief2026_extraction.csv"), rows, FIELDS)
    return rows
