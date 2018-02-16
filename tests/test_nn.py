import logging

from forecaster.predict.neural import NeuralNetwork


def main():
    logging.getLogger('forecaster').setLevel(logging.DEBUG)
    NN = NeuralNetwork('10_day')
    NN.train()


if __name__ == "__main__":
    main()
