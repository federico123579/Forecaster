from forecaster.handler import Client


def test_init():
    Client()


class TestClient():
    def handle_request(self, event, **kw):
        return event

    def test_start(self):
        self._change_mode()
        Client().start()

    def test_refresh(self):
        Client().refresh()

    def test_open_pos(self):
        Client().open_pos('EURUSD', 'buy', 5000)

    def test_close_pos(self):
        pos = Client().api.positions[-1]
        Client().close_pos(pos)

    def test_close_all_pos(self):
        Client().open_pos('EURUSD', 'buy', 5000)
        Client().open_pos('EURUSD', 'buy', 5000)
        Client().close_all()

    def test_last_candler(self):
        prices = Client().get_last_candles('EURUSD', 5, '1h')
        assert isinstance(prices, list)

    def _change_mode(self):
        if Client()._state.mode == 'live':
            Client().swap()
