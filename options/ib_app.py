from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import TickerId
from ibapi.ticktype import TickTypeEnum
from threading import Thread, Event
import time
import pandas as pd
import numpy as np
import logging


class IBApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        EWrapper.__init__(self)

        self._connected = Event()
        self._done = Event()
        self.nextValidOrderId = None


        self.snapshots = {}
        self._snap_events = {}

        self.hist_data = {}
        self._hist_events = {}

        self.contract_details = {}
        self._cd_events = {}

        self.opt_params = {}
        self._opt_params_events = {}

        self.option_quotes = {}
        self._opt_quote_events = {}


    def nextValidId(self, orderId: TickerId):
        self.nextValidOrderId = orderId
        self._connected.set()

    def tickPrice(self, reqId: TickerId, tickType, price, attrib):
        snap = self.snapshots.setdefault(reqId, {})

        if price > 0:
            snap[tickType] = price


    def tickOptionComputation(self, reqId, tickType, tickAttrib, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta, undPrice):
        quote = self.option_quotes.setdefault(reqId, {})
       
        quote.update({
            'impliedVol': impliedVol if impliedVol and impliedVol > 0 else None,
            'delta': delta, 'gamma': gamma, 'vega': vega, 'theta': theta,
            'undPrice': undPrice
        })

    def historicalData(self, reqId, bar):
        self.hist_data.setdefault(reqId, []).append({
            'date': bar.date, 'open': bar.open, 'high': bar.high, 'low': bar.low,
            'close': bar.close, 'volume': bar.volume, 'wap': bar.wap, 'barCount': bar.barCount
        })

    def historicalDataEnd(self, reqId, start, end):
        ev = self._hist_events.get(reqId)
        if ev: ev.set()

    # ----- Contract Details (to get conId for option params) -----
    def contractDetails(self, reqId, details):
        self.contract_details.setdefault(reqId, []).append(details)

    def contractDetailsEnd(self, reqId):
        ev = self._cd_events.get(reqId)
        if ev: ev.set()

    # ----- Option chain parameters -----
    def securityDefinitionOptionalParameter(self, reqId, exchange, underlyingConId,
                                            tradingClass, multiplier, expirations, strikes):
        self.opt_params[reqId] = {
            'exchange': exchange,
            'underlyingConId': underlyingConId,
            'tradingClass': tradingClass,
            'multiplier': multiplier,
            'expirations': sorted(list(expirations)),
            'strikes': sorted(list(strikes))
        }

    def securityDefinitionOptionalParameterEnd(self, reqId):
        ev = self._opt_param_events.get(reqId)
        if ev: ev.set()

    def start(self, host = '127.0.0.1', port = 7496, clientId = 1):
        self.connect(host, port, clientId)
        Thread(target=self.run, daemon=True).start()
        if not self._connected.wait(timeout=5):
            raise TimeoutError("Failed to connect to TWS/Gateway.")

    def stop(self):
        self.disconnect()