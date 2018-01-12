# -*- coding: utf-8 -*-

"""
bitgen.view.tele
~~~~~~~~~~~~~~

This module provides telegram integration.
"""

import telegram
from telegram import Bot
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler
from telegram.ext.filters import Filters
from bitgen.view.glob import OmniViewer, DefaultViewer

# logging
import logging
logger = logging.getLogger('bitgen.view.tele')


class TeleViewer(DefaultViewer):
    """telegram handler"""
    def __init__(self, supervisor):
        super().__init__(supervisor)
        self.token = OmniViewer().security['telegram-token']
        self.bot = Bot(token=self.token)
        self.updater = Updater(token=self.token)
        self.dispatcher = self.updater.dispatcher
        logger.debug("telegram viewer initiated")

    def listen(self):
        """listen every connections"""
        handlers = []  # append every command
        handlers.append(ConversationHandler(
            entry_points=[CommandHandler('config', self.cmd_config)],
            states={'api_key':
                    [MessageHandler(Filters.text, self.api_key, pass_chat_data=True)]},
            fallbacks=[CommandHandler('cancel', ConversationHandler.END)]))
        handlers.append(CommandHandler('predict', self.cmd_predict))
        handlers.append(CommandHandler('start', self.cmd_start))
        handlers.append(CommandHandler('stop', self.cmd_stop))
        handlers.append(CommandHandler('restart', self.cmd_restart))
        for hand in handlers:
            self.dispatcher.add_handler(hand)
        self.updater.start_polling()  # listen connections

    def cmd_start(self, bot, update):
        logger.debug("start command caught")
        self.chat_id = update.message.chat_id
        update.message.reply_text("Starting...")
        self.notify_observers('start-bot')
        update.message.reply_text("Bot started")

    def cmd_stop(self, bot, update):
        logger.debug("stop command caught")
        update.message.reply_text("Stopping...")
        self.notify_observers('stop-bot')
        update.message.reply_text("Bot stopped")

    def cmd_restart(self, bot, update):
        logger.debug("restart command caught")
        update.message.reply_text("Restarting...")
        self.notify_observers('stop-bot')
        self.notify_observers('start-bot')
        update.message.reply_text("Bot restarted")

    def cmd_config(self, bot, update):
        logger.debug("config command caught")
        update.message.reply_text("Bot configuration. This is for logging in coinbase.")
        update.message.reply_text("Please insert your api_key")
        return 'api_key'

    def cmd_predict(self, bot, update):
        logger.debug("predict command caught")
        update.message.reply_text("Predicting trend...")
        self.notify_observers('predict')

    def api_key(self, bot, update, chat_data):
        chat_data['api'] = update.message.text
        OmniViewer().pers_data['oneforge-api'] = chat_data['api']
        logger.debug("%s" % OmniViewer().pers_data)
        OmniViewer().collection['PERS_DATA'].save()
        update.message.reply_text("Configuration saved")
        return ConversationHandler.END

    def config_needed(self):
        logger.debug("configuration needed")
        self.bot.send_message(chat_id=self.chat_id, text="Configuration needed to continue")
        raise

    def out_pred(self, pred_dict):
        logger.debug("prediction processed")
        text = "Prediction:"
        for key in pred_dict.keys():
            text += "\nTiming: %d hours" % int(key)
            for curr in ['EURUSD', 'USDCHF', 'GBPUSD', 'USDJPY', 'USDCAD']:
                text += '\n_%s_ - *%.3f*' % (curr, pred_dict[key][curr])
        self.bot.send_message(chat_id=self.chat_id, text=text,
                              parse_mode=telegram.ParseMode.MARKDOWN)


# # Create a button menu to show in Telegram messages
# def build_menu(buttons, n_cols=1, header_buttons=None, footer_buttons=None):
#     menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
#
#     if header_buttons:
#         menu.insert(0, header_buttons)
#     if footer_buttons:
#         menu.append(footer_buttons)
#
#     return menu
#
#
# # Custom keyboards
# def keyboard_confirm():
#     buttons = [
#         KeyboardButton("YES"),
#         KeyboardButton("NO")
#     ]
#
#     return ReplyKeyboardMarkup(build_menu(buttons, n_cols=2))
