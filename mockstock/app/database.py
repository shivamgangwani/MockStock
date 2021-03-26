# This contains some db related functions that are frequently used
# during the code, mainly for getting mkt data or user data

import sqlite3
import os
import numpy as np
from flask import g

print_queries = False

sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))
THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(THIS_FOLDER,'data/database.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    if(print_queries==True):
        db.set_trace_callback(print)
    return db

def GetMarketStatus():
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute("SELECT * FROM config;")
    result = c.fetchall()
    c.close()
    result = dict(result)
    return result


def GetUserData(userid):
    data = dict()
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute("SELECT currency_id, amount FROM currency_portfolio WHERE user_id=?;", (userid, ) )
    data['currency_holding'] = c.fetchall()

    data['stock_holding'] = {}
    c.execute("SELECT stock_id, qty, book_value from stock_portfolio WHERE user_id=?;", (userid, ) )
    result = c.fetchall()

    for i in result:
        data['stock_holding'][i['stock_id']] = {'qty':i['qty'], 'book_value':i['book_value'] }

    c.close()
    data['currency_holding'] = dict(data['currency_holding'])
    return data

def GetStockPrices():
    data = {}
    db = get_db()
    db.row_factory = sqlite3.Row
    c = db.cursor()
    c.execute("SELECT * FROM stock_prices;")
    result = c.fetchall()
    c.close()

    for i in result:
        data[ i['stockID'] ] = {'opening_price':i['opening_price'], 'current_price':i['current_price']}
    
    return data
