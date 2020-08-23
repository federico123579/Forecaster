# ~~~~ main.py ~~~~
#  forecaster.main
# ~~~~~~~~~~~~~~~~~

from threading import Event

import click
from foreanalyzer.utils import SingletonMeta
import XTBApi.exceptions as xtbexc

from forecaster.bot import ForeBot
from forecaster.console import ForeCliConsole
import forecaster.exceptions as exc
from forecaster.interface import TelegramHandler
from forecaster.log_summary import LogRecap
from forecaster.thread_control import LogThread, ThreadHandler, wait

# ~ * DEBUG * ~
def DEBUG(text, level=1):
    ForeCliConsole().debug(text, "main", level)

def INFO(text):
    ForeCliConsole().info(text, "main")

def WARN(text):
    ForeCliConsole().warn(text, "main")

def ERROR(text):
    ForeCliConsole().error(text, "main")


# ~ * STATUS SINGLETON * ~
class STATUS(metaclass=SingletonMeta):
    """hold every important status for Mediator"""
    def __init__(self):
        self.bot = Event() # bot start and stop
        self.telegram = 0 # 0 stopped - 1 started       


# ~ * MEDIATOR INTERFACE * ~
class Mediator(object):
    """mediate between bot and telegram"""
    def __init__(self, telegram_token, **kwargs):
        self.bot = ForeBot(mediator=self, **kwargs)
        self.telegram = TelegramHandler(
            token=telegram_token, mediator=self)

    def alert(self, text):
        """send message to telegram"""
        self.telegram.send_msg(text)

    def main_loop(self):
        """entire loop from self.bot.bot_step_loop"""
        while STATUS().bot.is_set():
            try:
                self.bot.bot_loop_step()
            except exc.MarketClosed as e:
                wait(e.time_to_open, STATUS().bot)
            except Exception as e:
                ERROR(e)
                self.alert(
                    "**BOT STOPPED DUE TO AN EXCEPTION, MANUAL OPERATION REQUIRED**")
                self.shutdown()
                return
    
    def shutdown(self):
        self.stop_bot()
        ThreadHandler().stop_all()
        self.bot.terminate()

    def start_bot(self):
        """start the main loop"""
        if STATUS().bot.is_set():
            INFO('bot is working in the moment')
            return
        STATUS().bot.set()
        ThreadHandler().add_event(STATUS().bot)
        thread = LogThread(target=self.main_loop)
        thread.start()
        ThreadHandler().add_thread(thread, 'main_loop')
        INFO("main_loop Thread started and operative")
    
    def start_listening(self):
        """telegram: start listening to commands
        - CALLED BY: bot"""
        if STATUS().telegram == 0:
            self.telegram.activate()
        else:
            WARN("telegram is already listening")
    
    def stop_bot(self):
        """stop the main loop"""
        if not STATUS().bot.is_set():
            INFO('bot already stopped')
        STATUS().bot.clear()
        ThreadHandler().stop_all()
        DEBUG("bot stopped")


# ~~~ * MAIN COMMAND * ~~~~
@click.group()
@click.option('-v', '--verbose', count=True, default=0, show_default=True)
def main(verbose):
    ForeCliConsole().verbose = verbose

@main.command()
def run():
    main = Mediator(
        telegram_token='548272219:AAHo1jOMFNJ5A3TzPLhzqwm-qBCwEYVbJ7g',
        username='11361612',
        password='TestTest1.',
        mode='demo',
        instrument='EURUSD',
        volume_percentage=0.4)
    try: # TODO: try anc catch all exceptions
        main.bot.setup() # set up the bot, starts the api client
        main.start_listening()
    except xtbexc.NoInternetConnection:
        ERROR("no internet connection")
        return
    except OSError:
        ERROR("OSError: internet may be too slow")
        return

@main.command()
def logsummary():
    """digest logfile and make a summary"""
    log_recap = LogRecap()
    log_recap.main()

#ForeCliConsole().verbose = 3
#run()