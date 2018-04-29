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
class Chainer(metaclass=abc.ABCMeta):
    """
    Define an interface for handling requests.
    Implement the successor link.
    """

    def __init__(self):
        self._successor = None

    def attach_successor(self, successor):
        self._successor = successor

    def echo_request(self, chainer, request, **kwargs):
        return chainer.handle_request(request, **kwargs)

    def pass_request(self, request, **kwargs):
        if self._successor is not None:
            return self._successor.handle_request(request, **kwargs)

    @abc.abstractmethod
    def handle_request(self):
        pass


# -[ OBSERVER ]-
class Subject(object):
    """
    Know its observers. Any number of Observer objects may observe a
    subject.
    Send a notification to its observers when its state changes.
    """

    def __init__(self):
        self._observers = set()
        self._subject_state = None

    def attach_observer(self, observer):
        observer._subject = self
        self._observers.add(observer)

    def detach_observer(self, observer):
        observer._subject = None
        self._observers.discard(observer)

    def _notify(self):
        for observer in self._observers:
            observer.handle_notify(self._subject_state)

    @property
    def subject_state(self):
        return self._subject_state

    @subject_state.setter
    def subject_state(self, arg):
        self._subject_state = arg
        self._notify()


class Observer(metaclass=abc.ABCMeta):
    """
    Define an updating interface for objects that should be notified of
    changes in a subject.
    """

    def __init__(self):
        self._subject = None
        self._observer_state = None

    @abc.abstractmethod
    def handle_notify(self, arg):
        pass
