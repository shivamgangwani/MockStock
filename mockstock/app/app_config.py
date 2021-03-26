import os
import pandas as pd
import numpy as np

admin_name = 'admin'
admin_pass = 'password'

confirmation_window = 30 #inseconds

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
CURRENCY_DATA = os.path.join(THIS_FOLDER,'data/prereq/currencies.csv')
EXCHANGE_RATE_DATA = os.path.join(THIS_FOLDER,'data/prereq/exchange_rates.csv')
STOCKS_DATA = os.path.join(THIS_FOLDER,'data/prereq/stocks.csv')


exchange_rates = pd.read_csv(EXCHANGE_RATE_DATA, index_col=0)

NO_OF_ROUNDS = len(np.unique(exchange_rates['round']))
MAX_ROUNDS = NO_OF_ROUNDS #note that max rounds=2 means round can be 0 or 1, as counting starts from 0
MIN_ROUNDS = 0