# Note di progetto — calibrazione del motore

Questo file documenta come sono stati scelti i limiti numerici in
`engine.py`, perché il codice da solo non spiega perché quei numeri e non
altri. È parte della disciplina del progetto: nessuna scelta tecnica deve
restare arbitraria o non verificabile.

## Il problema

Un sistema a reazione-diffusione (Gray-Scott) può apparire stabile su un
orizzonte breve (poche centinaia di iterazioni) e poi collassare comunque
in uno stato uniforme e spento su un orizzonte più lungo. Il collasso è
uno stato assorbente: una volta che la concentrazione di V è ovunque
zero, nessun genoma successivo può farla ripartire, perché il termine di
reazione (U·V²) dipende da V stesso.

Una prima calibrazione, verificata solo su 260 iterazioni (un singolo
giorno), sembrava stabile ma collassava sistematicamente entro 3.000-4.000
iterazioni — cioè entro 12-15 giorni di vita simulata. Questo è stato
scoperto testando il genoma di default fissato, senza alcuna mutazione: se
anche un genoma costante muore, il problema non è nella logica di
mutazione ma nella fisica di base.

## La calibrazione corretta

Ogni combinazione di parametri qui sotto è stata verificata su un
orizzonte di almeno 16 × 260 = 4.160 iterazioni prima di essere accettata:

- **Du, Dv** (diffusione): i valori standard della letteratura sul modello
  Gray-Scott sono molto più piccoli di quanto intuitivo — Du ≈ 0.16,
  Dv ≈ 0.08, non Du ≈ 1.0 come in un primo tentativo. Sopra un rapporto
  Dv/Du di circa 0.6 il pattern si spegne sempre, indipendentemente da f
  e k.
- **f, k**: a Du=0.16, Dv=0.08, la regione viva a lungo termine è stretta:
  k deve stare tra circa 0.058 e 0.067; f ha più margine, tra circa 0.026
  e 0.060, ma la combinazione dei due deve restare vicina al centro di
  questa fascia.

I bound finali in `GENOME_BOUNDS` (`f`: 0.030–0.055, `k`: 0.059–0.066,
`Du`: 0.13–0.19, `Dv`: 0.065–0.095) sono più stretti della regione
teoricamente viva, per lasciare margine alla deriva cumulata di centinaia
di mutazioni successive senza avvicinarsi troppo al bordo.

## Il clip a riflessione

I parametri che toccano un limite non vengono troncati a muro (il che li
farebbe restare incollati esattamente sul bordo — la zona più instabile —
ogni volta che una mutazione li spinge oltre), ma riflessi all'indietro
dentro l'intervallo consentito. Questo è stato necessario dopo aver
osservato che il genoma di default iniziale, se appena fuori dai bound
correnti, veniva bloccato sul bordo per giorni consecutivi.

## Il meccanismo di reinnesco (`ensure_alive`)

Anche con questa calibrazione, il reinnesco resta come rete di sicurezza:
se in futuro i bound venissero allargati per esplorare forme diverse, o se
centinaia di migliaia di mutazioni cumulate portassero comunque verso un
bordo instabile, il sistema si reinnesca da solo invece di spegnersi per
sempre. Il reinnesco è deterministico (deriva solo da seed, etichetta del
gemello e numero del tentativo — mai da dati esterni) e viene sempre
registrato nel manifesto pubblico: non è un evento nascosto.

## Su questo tipo di verifica

Questa calibrazione è un esempio concreto di una regola del Documento IV:
un errore tecnico può travestirsi da coerenza apparente finché non lo si
mette sotto pressione per un tempo sufficiente. Un giorno di simulazione
sembrava una prova sufficiente. Non lo era. Vale la pena ricordarselo
anche fuori dal codice.
