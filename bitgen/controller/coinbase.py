# -*- coding: utf-8 -*-

"""
bitgen.controller.coinbase
~~~~~~~~~~~~~~

This module provides the interface for coinbase.
"""

from coinbase.wallet.client import Client
from bitgen.controller.glob import OmniController, DefaultController
from bitgen.controller.exceptions import *
from bitgen.exceptions import *

# logging
import logging
logger = logging.getLogger('bitgen.controller.coinbase')


class CoinbaseAPI(DefaultController):
    """API for coinbase"""
    def __init__(self, supervisor):
        super().__init__(supervisor)
        logger.debug("CoinbaseAPI initiated")

    def start(self):
        """start sequence"""
        self.login()  # login and init client
        self.refresh()  # update accounts

    def login(self):
        """log with credentials, need to be called after configuration"""
        try:
            OmniController().collection['PERS_DATA'].read()  # update
            api_key = OmniController().pers_data['coinbase-api']
            api_secret = OmniController().pers_data['coinbase-secret']
        except KeyError:
            raise MissingConfig()
        self.client = Client(api_key, api_secret)
        logger.debug("logged in")

    def refresh(self):
        """update every wallet"""
        self.accounts = self.client.get_accounts()['data']
        for acc in self.accounts:  # update wallets
            setattr(self, acc.balance.currency + '_wallet', acc)
        self.paymethods = self.client.get_payment_methods()['data']  # update payment methods
        logger.debug("refreshed")

    def get_price(self, mode, currency='EUR'):
        """get current price"""
        if mode == 'buy':
            price = float(self.client.get_buy_price()['amount'])
        elif mode == 'sell':
            price = float(self.client.get_sell_price()['amount'])
        exchange = float(self.client.get_exchange_rates()['rates'][currency])
        return price * exchange

    def deposit(self, amount, paymeth=None):
        """make a deposit"""
        # conditions
        paymeth = self._check_paymeth(paymeth)
        black_list = ['EUR Wallet']  # TODO: check if account type is related in someway
        try:  # use the first pay method
            paymeth = [x for x in self.paymethods if x.name not in black_list][0]
        except IndexError:
            raise ActionNotPermitted('deposit')
        if paymeth.allow_deposit is False:
            raise ActionNotPermitted('deposit')
        self.EUR_wallet.deposit(amount=amount, currency='EUR', payment_method=paymeth.id)
        logger.info("deposited %g EUR" % amount)

    def withdraw(self, amount, paymeth=None):
        """make a withdraw"""
        # conditions
        paymeth = self._check_paymeth(paymeth)
        if paymeth.allow_withdraw is False:
            raise ActionNotPermitted('withdraw')
        self.EUR_wallet.deposit(amount=amount, currency='EUR', payment_method=paymeth.id)
        logger.info("withdrawed %g EUR" % amount)

    def send_money(self, address, amount, currency):
        """send moeny to other address"""
        # conditions
        if currency not in [x.currency for x in self.accounts if x.currency != 'EUR']:
            raise ValueError(currency)
        wallet = getattr(self, currency + '_wallet')
        wallet.send_money(to=address, amount=amount, currency=currency)
        logger.info("sent %g %s to %s" % (amount, currency, address))

    def buy(self, amount, currency, paymeth=None):
        """buy a cryptocurrency"""
        # conditions
        if currency not in [x.currency for x in self.accounts]:
            raise ValueError(currency)
        paymeth = self._check_paymeth(paymeth)
        if paymeth.allow_buy is False:
            raise ActionNotPermitted('buy')
        wallet = getattr(self, currency + '_wallet')
        wallet.buy(amount=amount, currency=currency)
        logger.info("bought %g %s" % (amount, currency))

    def sell(self, amount, currency, paymeth=None):
        """buy a cryptocurrency"""
        # conditions
        if currency not in [x.currency for x in self.accounts]:
            raise ValueError(currency)
        paymeth = self._check_paymeth(paymeth)
        if paymeth.allow_sell is False:
            raise ActionNotPermitted('sell')
        wallet = getattr(self, currency + '_wallet')
        wallet.sell(amount=amount, currency=currency)
        logger.info("sold %g %s" % (amount, currency))

    def _check_paymeth(self, paymeth):
        if paymeth in [x.id for x in self.paymethods]:
            paymeth = [x for x in self.paymethods if x.id == paymeth][0]
        else:  # use the first pay method
            paymeth = self.paymethods[0]
        return paymeth
