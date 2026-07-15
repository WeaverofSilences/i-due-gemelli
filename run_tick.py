"""
run_tick.py — Esegue un singolo giorno di vita per entrambi i gemelli.

Uso:
    python run_tick.py --seed "il-tuo-seed-segreto-o-pubblico"

Al primo avvio (nessuno stato salvato) inizializza il giorno 0 con campo
identico per i due gemelli. Ad ogni avvio successivo:

  1. carica lo stato salvato di ieri (campo + genoma) per A e per B;
  2. legge la pressione di engagement del giorno per B (engagement.py);
  3. muta i due genomi (tick.py) — A non riceve mai l'engagement;
  4. avanza la fisica di entrambi i campi sotto il nuovo genoma;
  5. renderizza, salva le immagini, calcola l'hash SHA-256 di ognuna;
  6. aggiunge una riga al registro pubblico data/manifest.json;
  7. salva lo stato per il prossimo giorno.

Questo file non decide nulla di artistico. Applica soltanto, in ordine,
le regole scritte altrove.
"""

import argparse
import hashlib
import json
import os
from datetime import date, datetime, timezone

import numpy as np

import engine
import tick
import engagement

STATE_DIR = "data/state"
IMAGES_DIR = "data/images"
MANIFEST_PATH = "data/manifest.json"


def _load_manifest() -> list:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    return []


def _save_manifest(manifest: list) -> None:
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)


def _state_paths(twin: str):
    return (
        os.path.join(STATE_DIR, f"genome_{twin}.json"),
        os.path.join(STATE_DIR, f"field_{twin}.npz"),
    )


def _load_state(twin: str, seed: str):
    genome_path, field_path = _state_paths(twin)
    if os.path.exists(genome_path) and os.path.exists(field_path):
        with open(genome_path, "r", encoding="utf-8") as fh:
            genome = json.load(fh)
        data = np.load(field_path)
        return genome, data["U"], data["V"]
    # giorno 0: stato identico per costruzione
    U, V = engine.init_field(seed)
    return dict(engine.DEFAULT_GENOME), U, V


def _save_state(twin: str, genome: dict, U: np.ndarray, V: np.ndarray) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    genome_path, field_path = _state_paths(twin)
    with open(genome_path, "w", encoding="utf-8") as fh:
        json.dump(genome, fh, indent=2)
    np.savez_compressed(field_path, U=U, V=V)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def run(seed: str) -> None:
    manifest = _load_manifest()
    day = len(manifest)  # giorno 0 se il registro e' vuoto

    genome_A, U_A, V_A = _load_state("A", seed)
    genome_B, U_B, V_B = _load_state("B", seed)

    eng = engagement.get_engagement_score()

    if day > 0:
        genome_A = tick.mutate_A(genome_A, seed, day)
        genome_B = tick.mutate_B(genome_B, seed, day, eng["score"])
    # al giorno 0 nessuna mutazione: e' il seme comune.

    U_A, V_A = engine.run_steps(U_A, V_A, genome_A)
    U_B, V_B = engine.run_steps(U_B, V_B, genome_B)

    U_A, V_A, revived_A = engine.ensure_alive(U_A, V_A, genome_A, seed, "A")
    U_B, V_B, revived_B = engine.ensure_alive(U_B, V_B, genome_B, seed, "B")

    os.makedirs(IMAGES_DIR, exist_ok=True)
    img_A_path = os.path.join(IMAGES_DIR, f"day_{day:04d}_A.png")
    img_B_path = os.path.join(IMAGES_DIR, f"day_{day:04d}_B.png")
    engine.render(V_A, genome_A).save(img_A_path)
    engine.render(V_B, genome_B).save(img_B_path)

    entry = {
        "day": day,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "twin_a": {
            "genome": genome_A,
            "image": img_A_path,
            "sha256": _sha256_file(img_A_path),
            "revival_attempts": revived_A,
        },
        "twin_b": {
            "genome": genome_B,
            "image": img_B_path,
            "sha256": _sha256_file(img_B_path),
            "engagement": eng,
            "revival_attempts": revived_B,
        },
    }
    manifest.append(entry)
    _save_manifest(manifest)

    _save_state("A", genome_A, U_A, V_A)
    _save_state("B", genome_B, U_B, V_B)

    print(f"[run_tick] giorno {day} completato. "
          f"engagement={eng['score']} (voti={eng['votes']}, vendite={eng['sales']})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--seed", required=True,
        help="Seed del progetto. Va scelto una volta e non deve mai cambiare.",
    )
    args = parser.parse_args()
    run(args.seed)
