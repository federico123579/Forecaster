"""
forecaster.patterns
~~~~~~~~~~~~~~

Contains all design patterns.
"""

import abc


# +----------------------------------------------------------------------+
# | DESIGN PATTERNS                                                      |
# +----------------------------------------------------------------------+
# -[ SINGLETON ]-
class Singleton(type):
    """
    Define an Instance operation that lets clients access its unique
    instance.
    """

    def __init__(cls, name, bases, attrs, **kwargs):
        super().__init__(name, bases, attrs)
        cls._instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


# -[ CHAINER ]-
class Chainer():
    """
    Define an interface for handling requests.
    Implement the successor link.
    """

    def __init__(self, successor=None, **kw):
        self._successor = successor
        super().__init__(**kw)

    def echo_request(self, chainer, request, **kwargs):
        return chainer.handle_request(request, **kwargs)

    def pass_request(self, request, **kwargs):
        if self._successor is not None:
            return self._successor.handle_request(request, **kwargs)

    def handle_request(self):
        raise NotImplementedError()


# -[ STATER ]-
class StateContext():
    """
    Define the interface of interest to clients.
    Maintain an instance of a ConcreteState subclass that defines the
    current state.
    """

    def __init__(self, state, **kw):
        self._state = state
        super().__init__(**kw)

    def set_state(self, state):
        self._state = state

    def handle_state(self, action=None):
        self._state.handle(self, action)


class State(metaclass=abc.ABCMeta):
    """
    Define an interface for encapsulating the behavior associated with a
    particular state of the Context.
    """

    @abc.abstractmethod
    def handle(self):
        pass
