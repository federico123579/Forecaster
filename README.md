# Forecaster

Un software progettato per prevedere l'andamento di valute **forex** nell'arco di poco tempo. Grazie ai network neurali e al _Deep Learning_ tutto ciò non è più fantascienza, ma bensì è una grande possibilità di guadagno.

## Developing

Verranno utilizzati diversi _Design Patterns_:
- creational: **```singleton```**, **```builder```**
- structural: **```mvc```**, **```composite```**
- behavioral: **```observer```**, **```strategy```**

### Main Libraries

- Keras LSTM Network
- Telegram API
- Trading212 API (in futuro)

Il software si appoggierà sulle API di telegram per ricevere comandi che verranno elaborati e processati sul _Client_, in modo da renderlo _serverless_.

### WorkFlow

#### ```Model```

Ci saranno più fasi di aggiornamento:

1. manda una richiesta per le ultime 10 ore di prezzo
2. ogni 2 minuti aggiorna i prezzi di ciascun scabio valute
  - Per limiti imposti dal servizio di aggiornamento prezzi il massimo di richieste giornaliere ammontano a 1000
3. ogni ora calcola il minimo, il massimo, il prezzo di apertura e chiusura
4. aggiunge alla tabella dei 10 _records_ il valore ricavato
