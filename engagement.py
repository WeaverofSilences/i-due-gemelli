"""
engagement.py — Raccolta del segnale di riconoscimento per il Gemello B.

Principio dichiarato: solo eventi espliciti contano. Niente tracciamento
passivo di visite, niente fingerprinting, niente cookie di terze parti.

Due fonti, entrambe opt-in da parte di chi guarda:

1. Voti: un click esplicito su "vota questa forma" nel sito, raccolto da
   un piccolo Cloudflare Worker (vedi cloudflare/worker.js) e azzerato ad
   ogni tick.
2. Vendite: registrate a mano dall'artista in data/sales_log.json, perche'
   le vendite avvengono su un servizio print-on-demand esterno che questo
   progetto non deve automatizzare o osservare di nascosto.

Il punteggio finale e' una combinazione semplice e pubblica, non un
modello. La soglia EXPECTED_MAX_VOTES stabilisce quanti voti in un
giorno equivalgono a "pressione massima": va aggiustata nel tempo in
modo trasparente, annotando ogni cambiamento nel README.
"""

import json
import os
from datetime import date

import requests

EXPECTED_MAX_VOTES = 20     # voti/giorno equivalenti a pressione piena
SALE_WEIGHT = 5              # una vendita pesa quanto 5 voti

WORKER_COUNTS_URL = os.environ.get("PANTALEO_WORKER_URL", "")
WORKER_SECRET = os.environ.get("PANTALEO_WORKER_SECRET", "")

SALES_LOG_PATH = "data/sales_log.json"


def _fetch_votes() -> int:
    """Legge e azzera il contatore di voti dal Worker. 0 se non configurato."""
    if not WORKER_COUNTS_URL:
        return 0
    try:
        resp = requests.get(
            WORKER_COUNTS_URL,
            headers={"Authorization": f"Bearer {WORKER_SECRET}"},
            timeout=10,
        )
        resp.raise_for_status()
        return int(resp.json().get("votes", 0))
    except Exception as exc:  # noqa: BLE001 — non deve mai bloccare il tick
        print(f"[engagement] impossibile leggere i voti: {exc}")
        return 0


def _sales_today() -> int:
    """Legge le vendite del giorno corrente da un file curato a mano."""
    if not os.path.exists(SALES_LOG_PATH):
        return 0
    with open(SALES_LOG_PATH, "r", encoding="utf-8") as fh:
        log = json.load(fh)
    today = date.today().isoformat()
    return int(log.get(today, 0))


def get_engagement_score() -> dict:
    """
    Ritorna il punteggio normalizzato e i dati grezzi, per trasparenza
    nel manifest pubblico.
    """
    votes = _fetch_votes()
    sales = _sales_today()

    raw_pressure = votes + sales * SALE_WEIGHT
    score = min(1.0, raw_pressure / EXPECTED_MAX_VOTES)

    return {
        "votes": votes,
        "sales": sales,
        "score": round(score, 4),
    }
