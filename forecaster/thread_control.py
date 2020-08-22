# ~~~~ thread_control.py ~~~~
#  forecaster.thread_control
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~

from threading import Thread, Event
import time

from foreanalyzer.utils import SingletonMeta

from forecaster.console import ForeCliConsole


# ~ * DEBUG * ~
def DEBUG(text, level=1):
    ForeCliConsole().debug(text, "thread", level)

def ERROR(text):
    ForeCliConsole().error(text, "thread")

def EXCEPTION(e):
    ForeCliConsole().exception(e, "thread")


# ~ * LOW LEVEL UTILITY FUNCTIONS * ~
def wait(timeout, event):
    """wait until loop or timeout clears"""
    DEBUG("sleeping for {} seconds".format(int(timeout)))
    start = time.time()
    while time.time() - start <= timeout and event.is_set():
        time.sleep(0.1)


class LogThread(Thread):
    """Thread class to handle errors"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._real_run = self.run
        self.run = self._wrap_run
        self._real_join = self.join
        self.join = self._wrap_join

    def _wrap_run(self):
        try:
            self._real_run()
        except Exception as e:
            ERROR('Exception in thread')
            EXCEPTION(e)

    def _wrap_join(self, *args, **kwargs):
        self._real_join(*args, **kwargs)
        DEBUG("thread: {!s} - joined".format(self))


class ThreadHandler(metaclass=SingletonMeta):
    def __init__(self):
        self.threads = {}
        self.events = []
        DEBUG("ThreadHandler initied")

    def add_thread(self, thr, id):
        """add thread"""
        if id in [k for k in self.threads.keys()]:
            DEBUG("thread: {!s} - already added, joining and replacing".format(thr))
            self.threads[id].join()
            self.threads[id] = thr
            return
        if isinstance(thr, Thread):
            self.threads[id] = thr
            DEBUG("thread: {!s} - added".format(thr))
        else:
            raise ValueError("{} is not a thread".format(thr))

    def add_event(self, event):
        """add event"""
        if event in self.events:
            DEBUG("event: {!s} - already added".format(event))
            return
        if isinstance(event, Event):
            self.events.append(event)
            DEBUG("event: {!s} - appended".format(event))
        else:
            raise ValueError("{} is not an event".format(event))

    def stop_all(self, timeout=None):
        """stop all events"""
        for ev in self.events:
            ev.clear()
            DEBUG("event: {!s} - cleared".format(ev))
        for _, thr in self.threads.items():
            thr.join(timeout)
            if not isinstance(thr, LogThread):
                DEBUG("thread: {!s} - joined".format(thr))
