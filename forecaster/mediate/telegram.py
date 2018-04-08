"""
forecaster.mediate.telegram
~~~~~~~~~~~~~~

Handle telegram requests and interface with the service.
"""

import json
import logging
import textwrap

import telegram
from forecaster.enums import ACTIONS
from forecaster.handler import Client
from forecaster.patterns import Chainer
from forecaster.utils import get_json, save_json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut
from telegram.ext import (CallbackQueryHandler, CommandHandler,
                          ConversationHandler, MessageHandler, Updater)
from telegram.ext.filters import Filters

LOGGER = logging.getLogger('forecaster.mediate.telegram')


class TelegramMediator(Chainer):
    """telegram interface"""

    def __init__(self, token, proxy):
        super().__init__(proxy)
        self.bot = telegram.Bot(token=token)
        self.updater = Updater(token=token)
        self.dispatcher = self.updater.dispatcher
        self._handlers = []

    def handle_request(self, event, **kw):
        return self.pass_request(event, **kw)

    def handle_query(self, bot, update):
        """CallbackQueryHandler"""
        query = update.callback_query
        data = json.loads(query.data)

        def change_msg(text):
            bot.edit_message_text(text=text, chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  parse_mode=telegram.ParseMode.MARKDOWN)

        if data['event'] == 'change_mode':
            if self.handle_request(ACTIONS.CHANGE_MODE, mode=data['mode']):
                change_msg("Changed mode to *{}*".format(data['mode']))
            else:
                change_msg("Failed to change mode to *{}*".format(data['mode']))

    def activate(self):
        """listen to connections"""
        # conversations
        self._handlers.append(ConversationHandler(
            entry_points=[CommandHandler('config', self.cmd_config)],
            states={'username_key':
                    [MessageHandler(
                        Filters.text, self.username_key, pass_chat_data=True)],
                    'password_key':
                    [MessageHandler(Filters.text, self.password_key, pass_chat_data=True)]},
            fallbacks=[CommandHandler('cancel', ConversationHandler.END)]))
        # callback_query
        self._handlers.append(CallbackQueryHandler(self.handle_query))
        # simple commands
        self._add_command('changemode', self.cmd_change_mode)
        self._add_command('closeall', self.cmd_close_all)
        self._add_command('valued', self.cmd_valued)
        self._add_command('funds', self.cmd_funds)
        self._add_command('results', self.cmd_results)
        self._add_command('whoami', self.cmd_who_am_i)
        self._add_command('help', self.cmd_help)
        self._add_command('restart', self.cmd_restart)
        self._add_command('shutdown', self.cmd_shutdown)
        self._add_command('stop', self.cmd_stop)
        self._add_command('start', self.cmd_start)
        for hand in self._handlers:
            self.dispatcher.add_handler(hand)
        self.updater.start_polling()  # listen to connections
        LOGGER.debug("Telegram listening")

    def _add_command(self, name, func):
        self._handlers.append(CommandHandler(name, func))

    def deactivate(self):
        self.updater.stop()
        LOGGER.debug("Telegram stopped")

    def cmd_start(self, bot, update):
        LOGGER.debug("start command caught")
        self.chat_id = update.message.chat_id
        self.handle_request(ACTIONS.START_BOT)
        update.message.reply_text("Bot started")

    def cmd_stop(self, bot, update):
        LOGGER.debug("stop command caught")
        self.renew_connection()
        self.handle_request(ACTIONS.STOP_BOT)
        self.send_msg("Bot stopped")

    def cmd_shutdown(self, bot, update):
        LOGGER.debug("shutdown command caught")
        self.renew_connection()
        self.handle_request(ACTIONS.SHUTDOWN)

    def cmd_restart(self, bot, update):
        LOGGER.debug("restart command caught")
        self.renew_connection()
        self.send_msg("Restarting...")
        self.handle_request(ACTIONS.STOP_BOT)
        self.handle_request(ACTIONS.START_BOT)
        self.send_msg("Bot restarted")

    def cmd_help(self, bot, update):
        LOGGER.debug("help command caught")
        self.renew_connection()
        text = textwrap.dedent("""\
            Forecaster uses his algorithm to predict more profitable moments to make transactions.
            These are all commands avaible:
            - /help: print this
            - /start: start the bot
            - /stop: stop the bot
            - /config: start the configuration
            - /whoami: display username
            - /shutdown: shut the bot
            - /restart: restart the bot
            - /results: print the results from start
            - /funds: print the current free funds
            - /valued: print current values of transactions
            - /closeall: close all positions
            - /changemode: change mode of handler""")

        self.send_msg(text)

    def cmd_config(self, bot, update):
        LOGGER.debug("config command caught")
        self.send_msg("Bot configuration. This is for logging in trading212.")
        self.send_msg("Please insert your Trading212 username")
        return 'username_key'

    def username_key(self, bot, update, chat_data):
        chat_data['username'] = update.message.text
        self.credentials = {}
        self.credentials['username'] = chat_data['username']
        update.message.reply_text("Please insert password")
        return 'password_key'

    def password_key(self, bot, update, chat_data):
        chat_data['password'] = update.message.text
        self.credentials['password'] = chat_data['password']
        LOGGER.debug(self.credentials)
        save_json(self.credentials, get_json('data'))
        del self.credentials
        update.message.reply_text("Configuration saved")
        return ConversationHandler.END

    def cmd_results(self, bot, update):
        LOGGER.debug("results command caught")
        self.renew_connection()
        self.send_msg("Actual results are *{:.2f}*".format(Client().results))

    def cmd_funds(self, bot, update):
        LOGGER.debug("funds command caught")
        self.renew_connection()
        self.send_msg("Current free funds: *{}*".format(Client().funds['free']))

    def cmd_valued(self, bot, update):
        LOGGER.debug("valued command caught")
        self.renew_connection()
        Client().refresh()
        result = Client().api.account.funds['result']
        num_pos = len(Client().api.account.positions)
        self.send_msg(
            "Actual value is *{:.2f}* with *{}* positions".format(result, num_pos))

    def cmd_close_all(self, bot, update):
        LOGGER.debug("close_all command caught")
        self.renew_connection()
        Client().refresh()
        LOGGER.info("closing all positions")
        old_results = Client().results
        Client().close_all()
        profit = Client().results - old_results
        LOGGER.info("profit: {:.2f}".format(profit))
        self.send_msg(
            "Closed all positions with profit of *{:.2f}*".format(profit))

    def cmd_change_mode(self, bot, update):
        """change mode command"""
        LOGGER.debug("change_mode command caught")
        modes = ["live", "demo"]
        button_list = []
        for mode in modes:
            data = {'event': 'change_mode', 'mode': mode}
            button_list.append(InlineKeyboardButton(
                mode, callback_data=json.dumps(data)))
        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
        self.send_msg("Choose your *mode*:", reply_markup=reply_markup)

    def cmd_who_am_i(self, bot, update):
        LOGGER.debug("who_am_i command caught")
        text = "username: {}".format(Client().username)
        self.send_msg(text)

    def config_needed(self):
        LOGGER.debug("configuration needed")
        self.send_msg("Configuration needed to continue")

    def close_pos(self, result):
        LOGGER.debug("close_position telegram")
        self.renew_connection()
        LOGGER.debug("closed position - revenue of {:.2f}".format(result))
        self.send_msg("Closed position with gain of *{:.2f}*".format(result))

    def open_pos(self, number):
        LOGGER.debug("open_position telegram")
        self.renew_connection()
        LOGGER.debug("opened {:d} position".format(number))
        self.send_msg("Opened *{:d}* position".format(number))

    def close_all_pos(self, results):
        LOGGER.debug("close_all_position telegram")
        self.renew_connection()
        LOGGER.debug("closed all positions - revenue of {:.2f}".format(results))
        self.send_msg("Closed all positions - profit: *{:.2f}*".format(results))

    def send_msg(self, text, **kw):
        """send message with formatting"""
        self.bot.send_message(chat_id=self.chat_id, text=text,
                              parse_mode=telegram.ParseMode.MARKDOWN, **kw)

    def renew_connection(self):
        timeout = 5
        while timeout > 0:
            try:
                # get chat info to renew connection
                self.bot.getChat(chat_id=self.chat_id, timeout=1)
                break
            except TimedOut:
                LOGGER.error("Telegram timed out, renewing")
                timeout -= 1
        LOGGER.debug("renewed connection")


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    """build menu with given buttons"""
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu
