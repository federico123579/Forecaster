# Forecaster

Un software progettato per prevedere l'andamento di valute **forex** nell'arco di poco tempo. Grazie ai network neurali e al *Deep Learning* tutto ciò non è più fantascienza, ma bensì è una grande possibilità di guadagno.

## Developing

Verranno utilizzati diversi *Design Patterns*:
- creational: **```singleton```**, **```builder```**
- structural: **```mvc```**, **```composite```**
- behavioral: **```observer```**, **```strategy```**
### Main Libraries
- Keras LSTM Network
- Telegram API
- Trading212 API (in futuro)

Il software si appoggierà sulle API di telegram per ricevere comandi che verranno elaborati e processati sul *Client*, in modo da renderlo *serverless*.
