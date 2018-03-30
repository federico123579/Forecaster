import logging
from forecaster.handler import Client, SentryClient


def test_init():
    Client()


class TestClient():
    def test_start(self):
        self._change_mode()
        Client().start()

    def test_properties(self):
        assert isinstance(Client().positions, list)
        assert isinstance(Client().account, object)
        assert isinstance(Client().funds, dict)

    def test_refresh(self):
        Client().refresh()

    def test_open_pos(self, caplog):
        caplog.set_level(logging.DEBUG, logger="forecaster")
        SentryClient().captureException = lambda: True
        # test every instrument
        Client().open_pos('EURUSD_ZERO', 'buy', 5000)
        # test if market closed
        if "Market closed" in caplog.records[-1].message:
            return
        Client().open_pos('GBPUSD_ZERO', 'buy', 5000)
        Client().open_pos('USDCAD_ZERO', 'buy', 5000)
        Client().open_pos('USDCHF_ZERO', 'buy', 5000)
        Client().open_pos('USDJPY_ZERO', 'buy', 5000)
        # test over quantity
        Client().open_pos('EURUSD_ZERO', 'buy', 60000)
        assert "Maximum quantity exceeded" in caplog.records[-1].message
        Client().open_pos('EURUSD_ZERO', 'buy', 1000)
        assert "Minimum quantity exceeded" in caplog.records[-1].message
        # test too transactions
        Client().open_pos('EURUSD_ZERO', 'buy', 45000)
        Client().open_pos('EURUSD_ZERO', 'buy', 10000)
        assert "Product not avaible" in caplog.records[-1].message

    def test_close_pos(self):
        Client().open_pos('EURUSD_ZERO', 'buy', 5000)
        pos = Client().api.positions[-1]
        Client().close_pos(pos)

    def test_close_all_pos(self):
        Client().open_pos('EURUSD_ZERO', 'buy', 5000)
        Client().open_pos('EURUSD_ZERO', 'buy', 5000)
        Client().close_all()

    def test_last_candler(self):
        prices = Client().get_last_candles('EURUSD', 5, '1h')
        assert isinstance(prices, list)

    def test_get_margin(self):
        margin = Client().get_margin('EURUSD', 10)
        assert isinstance(margin, (int, float))

    def _change_mode(self):
        if Client().mode == 'live':
            Client().swap()
