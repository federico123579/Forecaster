import logging
import time

from forecaster import Bot

logger = logging.getLogger('forecaster.tests')


def main():
    logging.getLogger('forecaster').setLevel(logging.DEBUG)
    bot = Bot('mean_rev')  # init bot
    bot.handler.start()
    closes = bot.handler.get_last_closes('EURUSD', 100, '5m')  # get closes
    samples = []  # contains all samples
    for i in range(len(closes)):
        if i+5 <= len(closes):
            samples.append(closes[i:i+5])
    # test all samples
    predictions = []
    for sample in samples:
        predictions.append(bot.predict.MeanReversion.predict(sample))
    logger.info(predictions)


if __name__ == '__main__':
    main()
