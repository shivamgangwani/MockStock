import pandas as pd
import numpy as np
import os

from .app_config import CURRENCY_DATA, EXCHANGE_RATE_DATA, STOCKS_DATA, NO_OF_ROUNDS, MAX_ROUNDS, MIN_ROUNDS

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

currencies = {}
stocks = {}
BandProportions = {-1:0, 0:0.025, 1:0.05, 2:0.075}
valid_stockex_names = []
list_of_stocks_by_currID = {}

currency_data = pd.read_csv(CURRENCY_DATA, index_col=0)
exchange_rates = pd.read_csv(EXCHANGE_RATE_DATA, index_col=0)
stocks_data = pd.read_csv(STOCKS_DATA, index_col=0)



exchange_rates_complex = {}



######### CURRENCY MODEL ########
class Currency:
    def __init__(self, id, short_name, full_name, exchange_short, exchange_full, up_lim1, up_lim2, up_lim3):
        self.id=id
        self.short_name=short_name
        self.full_name=full_name
        self.exchange_short=exchange_short
        self.exchange_full=exchange_full
        self.up_lim={0: up_lim1, 1:up_lim2, 2:up_lim3} #2.5%, 5% and 7.5%

        valid_stockex_names.append(exchange_short)
        list_of_stocks_by_currID[id]=list()


for i in range( len(currency_data)):
    currencies[ currency_data.iloc[i, 0] ] = (
        Currency(currency_data.iloc[i, 0], currency_data.iloc[i, 1],
                currency_data.iloc[i, 2], currency_data.iloc[i, 3],
                currency_data.iloc[i, 4],
                currency_data.iloc[i, 5], currency_data.iloc[i, 6],
                currency_data.iloc[i, 7])
        )

def Curr_IDToShortName(id):
    return str( currency_data[ currency_data['id'] == id ]['currency'].values[0] )

def Curr_ShortNameToID(name):
    return int( currency_data[ currency_data['currency'] == name ]['id'].values[0] )

def Curr_ExchangeToID(name):
     return int( currency_data[ currency_data['exchange'] == name ]['id'].values[0] )



def ExchangeRate(round, curr_1, curr_2): #from curr_1 to curr_2
    if(curr_1==curr_2):
        return 1
    else:
        a=min(curr_1, curr_2)
        b=max(curr_1, curr_2)
        round=int(round)
        a_ = Curr_IDToShortName(a)
        b_ = Curr_IDToShortName(b)
        c = exchange_rates[ (exchange_rates['round']==round) & (exchange_rates['curr_1']==a_) & (exchange_rates['curr_2']==b_) ]
        c = float( c['amount'].values[0] )
        if(a==curr_1 and b==curr_2):
            return c
        else:
            return (1/c)


for r in range(NO_OF_ROUNDS): #loop over rounds
    exchange_rates_complex[r]={}
    for i in range(1, len(currencies)+1):
        exchange_rates_complex[r][i]={}
        for j in range(i, len(currencies)+1):
            exchange_rates_complex[r][i][j] = ExchangeRate(r, i, j)

currency_choices_form=[ (i.id, i.short_name) for i in list(currencies.values() ) ]




###### STOCKS MODEL #########
class Stock:
    def __init__(self, id, symbol, name, currency, initial_price):
        self.id=id
        self.symbol=symbol
        self.name=name
        self.currency=Curr_ShortNameToID(currency)
        self.initial_price=initial_price

        list_of_stocks_by_currID[ self.currency ].append(self)

for i in range( len(stocks_data)):
    stocks[ stocks_data.iloc[i, 0] ] = (
        Stock(stocks_data.iloc[i, 0], stocks_data.iloc[i, 1],
                stocks_data.iloc[i, 2], stocks_data.iloc[i, 3],
                stocks_data.iloc[i, 4])
        )


# Misc functions relating to the above classes...
def ListOfStocks(exchange):
    return list_of_stocks_by_currID[ Curr_ExchangeToID(exchange) ]

def GetCurrencyLimitBand(currency_id, amount):
    if(amount < currencies[currency_id].up_lim[0] ):
        return -1
    elif( currencies[currency_id].up_lim[0] <= amount < currencies[currency_id].up_lim[1] ):
        return 0
    elif( currencies[currency_id].up_lim[1] <= amount < currencies[currency_id].up_lim[2] ):
        return 1
    elif(amount >= currencies[currency_id].up_lim[2]):
        return 2

def GetProportionFromLimitBand(band):
    return BandProportions[band]

def IsValidStockExchange(shortname):
    return (shortname in valid_stockex_names)