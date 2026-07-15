"""
engine.py — Motore generativo condiviso dei due gemelli.

Implementa un sistema a reazione-diffusione (modello Gray-Scott).
Non contiene alcuna logica di mutazione: quella vive in tick.py.
Questo file definisce solo la fisica condivisa da cui i due gemelli
si allontanano nel tempo, e la sua resa visiva.

Il genoma di ogni gemello e' un dizionario di 8 numeri:

    f       tasso di alimentazione (feed rate)
    k       tasso di soppressione (kill rate)
    Du      diffusione della sostanza U
    Dv      diffusione della sostanza V
    hue_lo  tonalita' colore a bassa concentrazione di V   (0..1)
    hue_hi  tonalita' colore ad alta concentrazione di V   (0..1)
    sat     saturazione del colore                          (0..1)
    gamma   contrasto nella mappa colore                    (>0)
"""

import hashlib
import numpy as np
from PIL import Image
import colorsys

GRID_SIZE = 150          # lato della griglia di simulazione
STEPS_PER_DAY = 260       # iterazioni della PDE per ogni "giorno"
RENDER_SIZE = 640         # lato dell'immagine esportata (px)

GENOME_BOUNDS = {
    # Regione di sopravvivenza verificata su orizzonte LUNGO (16 x 260 =
    # 4160 step, non solo un giorno) — vedi note_di_progetto.md. Una
    # regione che sembra viva dopo un solo giorno di simulazione puo'
    # comunque spegnersi lentamente entro poche migliaia di step: per
    # questo la verifica e' stata rifatta su un orizzonte molto piu'
    # lungo di quello di un singolo tick.
    "f":      (0.030, 0.055),
    "k":      (0.059, 0.066),
    "Du":     (0.13, 0.19),
    "Dv":     (0.065, 0.095),
    "hue_lo": (0.0, 1.0),   # circolare
    "hue_hi": (0.0, 1.0),   # circolare
    "sat":    (0.30, 1.00),
    "gamma":  (0.60, 2.20),
}

DEFAULT_GENOME = {
    # Centro esatto della regione di sopravvivenza a lungo termine.
    "f": 0.0425,
    "k": 0.0625,
    "Du": 0.16,
    "Dv": 0.080,
    "hue_lo": 0.58,   # blu freddo
    "hue_hi": 0.02,   # rosso caldo
    "sat": 0.65,
    "gamma": 1.10,
}


def seed_hash(seed: str, *parts) -> str:
    """Hash deterministico di seed + parti aggiuntive. Nessun input esterno."""
    joined = ":".join([seed, *[str(p) for p in parts]])
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def det_unit(seed: str, *parts) -> float:
    """Numero pseudo-casuale deterministico in [-1, 1], derivato solo da seed+parti."""
    h = seed_hash(seed, *parts)
    val = int(h[:8], 16) / 0xFFFFFFFF
    return val * 2.0 - 1.0


def init_field(seed: str):
    """
    Campo iniziale, identico per costruzione ai due gemelli finche' non
    vengono chiamati separatamente: U=1 ovunque, V=0, con alcune macchie
    di innesco le cui posizioni derivano deterministicamente dal seed.
    """
    U = np.ones((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    V = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float64)

    n_blobs = 5
    for i in range(n_blobs):
        rx = (det_unit(seed, "init_x", i) + 1) / 2
        ry = (det_unit(seed, "init_y", i) + 1) / 2
        cx = int(rx * (GRID_SIZE - 20)) + 10
        cy = int(ry * (GRID_SIZE - 20)) + 10
        r = 4
        U[cy - r:cy + r, cx - r:cx + r] = 0.50
        V[cy - r:cy + r, cx - r:cx + r] = 0.25

    return U, V


def _laplacian(A: np.ndarray) -> np.ndarray:
    """Laplaciano discreto a 9 punti con condizioni al contorno periodiche."""
    return (
        -A
        + 0.20 * (
            np.roll(A, 1, axis=0) + np.roll(A, -1, axis=0)
            + np.roll(A, 1, axis=1) + np.roll(A, -1, axis=1)
        )
        + 0.05 * (
            np.roll(np.roll(A, 1, axis=0), 1, axis=1)
            + np.roll(np.roll(A, 1, axis=0), -1, axis=1)
            + np.roll(np.roll(A, -1, axis=0), 1, axis=1)
            + np.roll(np.roll(A, -1, axis=0), -1, axis=1)
        )
    )


def run_steps(U, V, genome, steps: int = STEPS_PER_DAY, dt: float = 1.0):
    """Avanza il campo (U, V) di `steps` iterazioni sotto la fisica del genoma dato."""
    f, k = genome["f"], genome["k"]
    Du, Dv = genome["Du"], genome["Dv"]
    for _ in range(steps):
        Lu, Lv = _laplacian(U), _laplacian(V)
        uvv = U * V * V
        U = U + (Du * Lu - uvv + f * (1.0 - U)) * dt
        V = V + (Dv * Lv + uvv - (f + k) * V) * dt
        np.clip(U, 0.0, 1.0, out=U)
        np.clip(V, 0.0, 1.0, out=V)
    return U, V


REVIVAL_THRESHOLD = 0.015  # sotto questa deviazione standard, il campo e' spento
REVIVAL_ATTEMPTS = 3


def _inject_blobs(U, V, seed: str, label: str, attempt: int):
    """Reinnesco deterministico: nuove macchie derivate solo da seed+etichetta+tentativo."""
    n_blobs = 4
    for i in range(n_blobs):
        rx = (det_unit(seed, label, "revive", attempt, "x", i) + 1) / 2
        ry = (det_unit(seed, label, "revive", attempt, "y", i) + 1) / 2
        cx = int(rx * (GRID_SIZE - 20)) + 10
        cy = int(ry * (GRID_SIZE - 20)) + 10
        r = 4
        U[cy - r:cy + r, cx - r:cx + r] = 0.50
        V[cy - r:cy + r, cx - r:cx + r] = 0.25
    return U, V


def ensure_alive(U, V, genome, seed: str, label: str):
    """
    Se il campo e' collassato in uno stato uniforme (assorbente per questa
    fisica: da V=0 ovunque non si puo' piu' risalire con nessun genoma),
    lo reinnesca con macchie deterministiche e fa ripartire la simulazione.

    Il reinnesco non e' un input dal mondo: dipende solo da seed, etichetta
    del gemello e numero del tentativo. Ogni reinnesco viene registrato dal
    chiamante nel manifest pubblico, non e' un evento nascosto.
    """
    attempts_used = 0
    for attempt in range(REVIVAL_ATTEMPTS):
        if float(V.std()) > REVIVAL_THRESHOLD:
            break
        U, V = _inject_blobs(U, V, seed, label, attempt)
        U, V = run_steps(U, V, genome, steps=STEPS_PER_DAY)
        attempts_used = attempt + 1
    return U, V, attempts_used


def render(V: np.ndarray, genome: dict) -> Image.Image:
    """Mappa il campo V a colore secondo il genoma. Nessun altro input."""
    v = V.copy()
    v_min, v_max = v.min(), v.max()
    if v_max - v_min > 1e-9:
        v = (v - v_min) / (v_max - v_min)
    v = np.power(np.clip(v, 0, 1), 1.0 / max(genome["gamma"], 1e-3))

    hue_lo, hue_hi = genome["hue_lo"], genome["hue_hi"]
    sat = genome["sat"]

    h, w = v.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    # interpolazione hue circolare + colorsys per pixel e' troppo lenta in
    # puro Python: vettorizziamo costruendo una lookup table a 256 livelli.
    lut = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        t = i / 255.0
        hue = (hue_lo + (hue_hi - hue_lo) * t) % 1.0
        r, g, b = colorsys.hsv_to_rgb(hue, sat, 0.15 + 0.85 * t)
        lut[i] = [int(r * 255), int(g * 255), int(b * 255)]

    idx = np.clip((v * 255).astype(np.uint8), 0, 255)
    rgb = lut[idx]

    img = Image.fromarray(rgb, mode="RGB")
    img = img.resize((RENDER_SIZE, RENDER_SIZE), Image.LANCZOS)
    return img
