<p align="center">
  <img src="./static/crystal_sphere.png" alt="Forecaster Logo">
</p>

# Forecaster

A trading software that use a mean reversion algorithm to predict trend in regolar time spans and make transaction to Trading212 broker service using the Trading212 APIs (that I've made before).

## Behavior

### Algorithm

The algorithm used is the Mean Reversion with this formula:

<p align="center">
  <img src="./static/formula-1.png" alt="Forecaster Logo">
</p>

with `avg` as a **price average**, `mult` for a **costant** and `dev` for a **deviation**. In my tests I found most effective the use of a _linear regression_ as `price average` and a finantial index named _Average True Range_ (that defines volatility) as `deviation`.

## How to install

Install just with pip:

``` bash
   pip install forecaster
```

Then run setup.sh to save the tokens needed by the software.

``` bash
   chmod +x setup.sh
   ./setup.sh
```

## Developing

Will be used these _Design Patterns_:

* creational: _`singleton`_, _`factory method`_
* structural: _`Proxy`_, `Adapter`, _`Decorator`_
* behavioral: _`Chain of responsability`_, _`Mediator`_, _`Strategy`_

### Main Libraries

* Telegram API
* Trading212 API

The `Bot` uses Telegram APIs to communicate with the user news and receive commands (asyncronously) and Trading212 API to make transactions and drive predictive algorithms.

### Backlog

To-Do list before the v1.0 release.

* [x] Tidy up code
* [x] Add thread handler
* [x] Add more telegram commands
* [x] Add market closure time watcher
* [ ] Add database integration
