# I due gemelli

Due processi generativi nati dallo stesso seme, lo stesso giorno.

**Gemello A** muta ogni giorno per una funzione deterministica interna:
seed e numero del giorno, nient'altro. Nessun dato del mondo entra nella
sua forma.

**Gemello B** muta per la stessa funzione, ma pesata dal riconoscimento
ricevuto il giorno prima — voti espliciti sul sito, vendite registrate a
mano. Più riconoscimento riceve, più la sua forma si sposta verso
contrasto e saturazione più alti.

Non c'è una tesi da spiegare: la divergenza tra i due, accumulata giorno
dopo giorno, è l'opera. Il registro pubblico (`site/index.html`) la mostra
senza commento.

Per il ragionamento completo dietro il progetto, vedi `note_di_progetto.md`.

## Struttura del progetto

```
engine.py       motore condiviso (reazione-diffusione, Gray-Scott)
tick.py         le due funzioni di mutazione — leggile, sono il cuore filosofico
engagement.py   raccoglie voti e vendite, normalizza il punteggio per B
run_tick.py     esegue un giorno di vita per entrambi i gemelli
data/           stato, immagini e registro pubblico (si popola da solo)
site/           il registro pubblico consultabile nel browser
cloudflare/      il piccolo servizio che raccoglie i voti
.github/workflows/  l'automazione che fa girare tutto, gratis, ogni giorno
```

## Mettere in funzione il progetto — da zero

Non serve un server. L'intera infrastruttura gira gratis su GitHub, più un
piccolo servizio gratuito Cloudflare solo per i voti.

### 1. Crea il repository

Crea un account GitHub se non ce l'hai (https://github.com), poi crea un
nuovo repository pubblico (es. `i-due-gemelli`) e carica dentro tutti i
file di questo progetto.

### 2. Scegli il seme — una volta sola

Il seme è la stringa da cui dipendono tutte le mutazioni di entrambi i
gemelli. **Va scelto una volta e non deve mai cambiare**, altrimenti la
continuità dei due organismi si rompe. Può essere una frase, una data, una
sequenza qualsiasi — l'importante è annotarla e non perderla.

Nel repository, vai su *Settings → Secrets and variables → Actions* e crea
un secret chiamato `PANTALEO_SEED` con il valore scelto.

### 3. Abilita GitHub Pages

*Settings → Pages → Source*, seleziona "GitHub Actions".

### 4. Abilita l'esecuzione schedulata

*Settings → Actions → General*, assicurati che le Actions siano abilitate
per il repository (di norma lo sono già di default).

Il workflow in `.github/workflows/daily-tick.yml` gira automaticamente una
volta al giorno. Per il primo giorno, o per testare subito, puoi lanciarlo
a mano da *Actions → tick quotidiano → Run workflow*.

### 5. Collega il meccanismo dei voti (facoltativo, puoi farlo dopo)

Segui `cloudflare/README-worker.md`. Senza questo passaggio il progetto
funziona comunque: il Gemello B semplicemente non riceve ancora nessuna
pressione, finché non colleghi il Worker.

### 6. Registra le vendite (facoltativo)

Quando vendi una stampa, aggiungi una riga a `data/sales_log.json` con la
data e il numero di vendite di quel giorno. Non è automatizzato apposta:
le vendite avvengono su un servizio esterno che questo progetto non deve
osservare o automatizzare di nascosto.

## Verificare l'autenticità di un'immagine

Ogni voce di `data/manifest.json` contiene l'hash SHA-256 dell'immagine
del giorno. Per verificare che un file non sia stato alterato:

```
sha256sum data/images/day_0042_A.png
```

Il valore deve coincidere con quello nel manifesto. La cronologia dei
commit Git dà inoltre una prova temporale indipendente di quando ogni
stato è stato generato.

## Costi

A regime: 0 € (GitHub Actions e Pages gratuiti nei limiti d'uso normali di
un progetto personale; Cloudflare Workers gratuito fino a 100.000
richieste al giorno). Un dominio personalizzato, se lo vuoi, costa
10-15 €/anno ed è del tutto facoltativo — puoi restare su
`tuonome.github.io` a lungo.

## Se il repository cresce troppo

Ogni giorno aggiunge due immagini PNG da 640×640px. Dopo alcuni anni la
dimensione del repository può diventare importante. Quando succede, le
opzioni più semplici sono: ridurre `RENDER_SIZE` in `engine.py` per le
immagini future, oppure spostare le immagini più vecchie di un anno su uno
storage esterno economico (es. Backblaze B2), lasciando nel repository
solo il manifesto e gli hash — che restano comunque la prova di
autenticità, a prescindere da dove vive il file.
