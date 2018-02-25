import logging

from forecaster.predict.neural import NeuralPredicter


def main():
    logging.getLogger('forecaster').setLevel(logging.DEBUG)
    NN = NeuralPredicter('tests/10_day')
    NN.train()


if __name__ == "__main__":
    main()
