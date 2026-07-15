# Pubblicare il Worker dei voti

Questo pezzo è l'unico che non può stare interamente su GitHub, perché un
sito statico non può scrivere dati da solo. Cloudflare Workers ha un piano
gratuito ampio (100.000 richieste/giorno), più che sufficiente qui.

## 1. Crea l'account

Vai su https://dash.cloudflare.com/sign-up e crea un account gratuito.

## 2. Installa lo strumento da riga di comando (una volta sola)

Nel terminale, dentro la cartella `cloudflare/` di questo progetto:

```
npm install -g wrangler
wrangler login
```

Si aprirà il browser per autorizzare l'accesso al tuo account.

## 3. Crea lo spazio dati (KV namespace)

```
wrangler kv namespace create VOTES
```

Il comando stampa un `id`. Copialo: ti serve nel prossimo passo.

## 4. Crea il file di configurazione `wrangler.toml`

Nella cartella `cloudflare/`, crea un file chiamato `wrangler.toml` con questo contenuto,
sostituendo `IL_TUO_ID_QUI` con l'id ottenuto al passo 3:

```
name = "pantaleo-gemelli-voti"
main = "worker.js"
compatibility_date = "2024-01-01"

kv_namespaces = [
  { binding = "VOTES", id = "IL_TUO_ID_QUI" }
]
```

## 5. Imposta il segreto di lettura

Questo token protegge l'endpoint `/counts` da letture non autorizzate.
Scegli tu una stringa lunga e casuale (es. generata da un password manager)
e salvala:

```
wrangler secret put READ_SECRET
```

Ti verrà chiesto di incollare il valore. **Salvalo anche altrove**: ti serve
di nuovo tra un momento, per la GitHub Action.

## 6. Pubblica

```
wrangler deploy
```

L'output ti darà un URL tipo:

```
https://pantaleo-gemelli-voti.TUO-SOTTODOMINIO.workers.dev
```

## 7. Collega l'URL nei due punti che lo aspettano

- In `site/index.html`, sostituisci la riga
  `const WORKER_VOTE_URL = "";`
  con
  `const WORKER_VOTE_URL = "https://pantaleo-gemelli-voti.TUO-SOTTODOMINIO.workers.dev/vote";`

- Nelle impostazioni del repository GitHub (Settings → Secrets and
  variables → Actions), aggiungi due secret:
  - `PANTALEO_WORKER_URL` = `https://pantaleo-gemelli-voti.TUO-SOTTODOMINIO.workers.dev/counts`
  - `PANTALEO_WORKER_SECRET` = lo stesso valore scelto al passo 5

Da qui in poi il meccanismo è automatico: ogni voto sul sito incrementa il
contatore, e ogni tick giornaliero lo legge e lo azzera.

Se preferisci partire senza questo pezzo, va bene lo stesso: senza Worker
configurato, l'engagement del Gemello B resta a zero finché non colleghi
questo passaggio — il sistema funziona comunque, semplicemente B non
riceve ancora nessuna pressione.
