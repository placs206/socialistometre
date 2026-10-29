"""Unique module de transformation d'échelle (V2).

Règle : transformation affine fixe d'une échelle officielle [min, max] vers [0, 100],
    v100 = (v - min) × 100 / (max - min)        et sa réciproque  v = min + v100 × (max - min) / 100.
Les bornes viennent de la documentation officielle de l'édition (config/sources.json), jamais des données observées :
aucune normalisation min-max sur l'échantillon, aucun rang converti en score, aucune troncature (une valeur officielle
hors bornes — ex. score Freedom House négatif — reste hors bornes et est signalée).
Calcul en arithmétique décimale exacte (pas d'artefact binaire), arrondi à 6 décimales seulement si la division
n'est pas exacte (ex. libertés civiles FH /60).
"""
from decimal import Decimal, ROUND_HALF_EVEN

Q = Decimal("0.000001")


def _d(x):
    return x if isinstance(x, Decimal) else Decimal(str(x))


def to_100(v, mn, mx):
    v, mn, mx = _d(v), _d(mn), _d(mx)
    if mx <= mn:
        raise ValueError("échelle invalide")
    r = (v - mn) * Decimal(100) / (mx - mn)
    q = r.quantize(Q, rounding=ROUND_HALF_EVEN)
    return float(q if q != r else r)


def from_100(v100, mn, mx):
    v100, mn, mx = _d(v100), _d(mn), _d(mx)
    return float(mn + v100 * (mx - mn) / Decimal(100))


def describe(mn, mx):
    mn, mx = _d(mn), _d(mx)
    if mn == 0 and mx == 100:
        return "identité (échelle officielle déjà 0-100)"
    if mn == 0:
        f = Decimal(100) / mx
        fs = format(f.normalize(), "f") if (f * 1000) == (f * 1000).to_integral_value() else f"100/{mx}"
        return f"× {fs} (échelle officielle 0-{mx} → 0-100)"
    return f"(v − {mn}) × 100 / ({mx} − {mn})"


def in_scale(v, mn, mx):
    return _d(mn) <= _d(v) <= _d(mx)
