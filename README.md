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
- Trading212 API

Il software si appoggierà sulle API di telegram per ricevere comandi che verranno elaborati e processati sul _Client_, in modo da renderlo _serverless_.
