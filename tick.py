"""
tick.py — Le due funzioni di mutazione del genoma.

Questo e' il file che decide, letteralmente, la differenza filosofica
tra i due gemelli. Deve restare leggibile da chiunque, senza eccezioni:
se un giorno questa logica smettesse di poter essere spiegata a voce in
un minuto, sarebbe il segnale che qualcosa e' andato storto rispetto al
Fondamento del progetto.

Gemello A — autonomo:
    ad ogni giorno, ogni parametro del genoma si sposta di una quantita'
    pseudo-casuale che dipende SOLO dal seed iniziale e dal numero del
    giorno. Nessun dato del mondo entra in questa funzione.

Gemello B — dipendente:
    la stessa mutazione di base viene moltiplicata e orientata da un
    punteggio di "pressione del riconoscimento" (0..1), calcolato dai
    voti espliciti e dalle vendite registrate nel giorno precedente.
    Piu' il gemello B viene premiato, piu' la sua forma si muove verso
    contrasto e saturazione piu' alti — un'approssimazione semplice e
    dichiarata di "spingere verso cio' che ha funzionato".
"""

from engine import GENOME_BOUNDS, det_unit

# Quanto si sposta al massimo ogni parametro in un singolo giorno,
# in assenza di qualunque pressione esterna.
BASE_STEP = {
    # f, k, Du, Dv sono i parametri che governano la sopravvivenza del
    # pattern (vedi note_di_progetto.md): passi piccoli, proporzionati
    # all'ampiezza di ciascun range, per restare dentro la regione viva
    # anche dopo centinaia di mutazioni cumulate.
    "f": 0.0006,
    "k": 0.0004,
    "Du": 0.003,
    "Dv": 0.0015,
    # hue, saturazione e contrasto non incidono sulla sopravvivenza:
    # possono muoversi con passi piu' ampi.
    "hue_lo": 0.020,
    "hue_hi": 0.020,
    "sat": 0.030,
    "gamma": 0.050,
}

# Guadagno massimo applicato al passo di mutazione del Gemello B quando
# il punteggio di engagement e' 1.0 (massima pressione osservata).
ENGAGEMENT_GAIN = 2.0

# Spostamento aggiuntivo e direzionale che il Gemello B subisce quando
# riceve engagement: spinge verso forme piu' contrastate e sature,
# come approssimazione dichiarata di "cio' che attira attenzione".
ENGAGEMENT_BIAS = {
    "gamma": 0.05,
    "sat": 0.03,
}

CIRCULAR_PARAMS = {"hue_lo", "hue_hi"}


def _clip(name: str, value: float) -> float:
    """
    Riporta il valore dentro i limiti. Per i parametri circolari, wrap.
    Per gli altri, riflessione invece di troncamento a muro: un valore
    che sfonda il limite rimbalza dentro, cosi' il genoma non resta
    incollato esattamente sul bordo (la zona piu' instabile) ogni volta
    che una mutazione lo spinge oltre.
    """
    lo, hi = GENOME_BOUNDS[name]
    if name in CIRCULAR_PARAMS:
        return value % 1.0
    if value > hi:
        value = hi - (value - hi)
    elif value < lo:
        value = lo + (lo - value)
    return max(lo, min(hi, value))


def mutate_A(genome: dict, seed: str, day: int) -> dict:
    """Mutazione deterministica: funzione pura di (seed, day). Nessun altro input."""
    new_genome = {}
    for name, value in genome.items():
        delta = det_unit(seed, "A", day, name) * BASE_STEP[name]
        new_genome[name] = _clip(name, value + delta)
    return new_genome


def mutate_B(genome: dict, seed: str, day: int, engagement_score: float) -> dict:
    """
    Mutazione pesata dall'engagement.

    engagement_score deve essere gia' normalizzato in [0, 1] da chi chiama
    (vedi engagement.py). La formula e' intenzionalmente semplice: nessun
    modello opaco decide la forma, solo un moltiplicatore e un bias pubblici.
    """
    engagement_score = max(0.0, min(1.0, engagement_score))
    gain = 1.0 + ENGAGEMENT_GAIN * engagement_score

    new_genome = {}
    for name, value in genome.items():
        base_delta = det_unit(seed, "B", day, name) * BASE_STEP[name]
        bias = ENGAGEMENT_BIAS.get(name, 0.0) * engagement_score
        new_genome[name] = _clip(name, value + base_delta * gain + bias)
    return new_genome
