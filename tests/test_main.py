import logging
import time

from forecaster import Bot

logger = logging.getLogger('forecaster.tests')


def main():
    logging.getLogger('forecaster').setLevel(logging.DEBUG)
    bot = Bot('default')  # init bot
    bot.handler.start()
    candles = bot.handler.get_last_candles('EURUSD', 100, '1d')  # get candles
    samples = []  # contains all samples
    for i in range(len(candles)):
        if i+5 <= len(candles):
            samples.append(candles[i:i+5])
    # test all samples
    predictions = []
    for sample in samples:
        predictions.append(bot.predict.MeanReversion.predict(sample).value)
    logger.info(predictions)


if __name__ == '__main__':
    main()
