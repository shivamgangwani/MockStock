# This contains the database schema and some other config information...
# This file must be executed before the web app is started
# Note: execute with python3 command instead of python
# Note: DELETE PREREQ FILES BEFORE STARTING This
# ALSO DELETE DATABASE.DB BEFORE STARTING THIS

import sqlite3
import pandas as pd
import numpy as np
import os

# The players will be assigned one of the initial_portfolios
# intial_portfolio['stocks'/'currencies'][id] holds the initial qty of stock/currID held 
initial_portfolios = {
    0 : { 
        'stocks': {
            5:400, 
            1:300, 
            2:399, 
            6:528, 
            8:600, 
            3:450, 
            7:550, 
            4:349 
        }, 
        'currencies': {
            1:0, 
            2:4950000, 
            3:0, 
            4:0
        }
    },

    1 : { 
        'stocks': {
            5:350, 
            1:600, 
            2:550, 
            6:421, 
            8:378, 
            3:459, 
            7:400, 
            4:530 
        }, 
        'currencies': {
            1:3300000, 
            2:0, 3:0, 
            4:0 
        } 
    },

    2: { 
        'stocks': {
            5:200, 
            1:490, 
            2:598, 
            6:600, 
            8:337, 
            3:580, 
            7:610, 
            4:450 
        }, 
        'currencies': {
            1:0, 
            2:0, 
            3:0, 
            4:1633500 
        }
    },
    
    3: { 
        'stocks': {
            5:600, 
            1:250, 
            2:349, 
            6:400, 
            8:600, 
            3:300, 
            7:449, 
            4:298
        }, 
        'currencies': {
            1:0, 
            2:0, 
            3:8266500, 
            4:0
        } 
    }
}

THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))

sqlite3.register_adapter(np.int64, lambda val: int(val))
sqlite3.register_adapter(np.int32, lambda val: int(val))

DATABASE = os.path.join(THIS_FOLDER, 'app/data/database.db')

# Prereq file paths
PARTICIPANTS_DATA = os.path.join(THIS_FOLDER,'app/data/prereq_excel/participants.xlsx')
NEWS_DATA = os.path.join(THIS_FOLDER,'app/data/prereq_excel/news.xlsx')
CURRENCY_DATA = os.path.join(THIS_FOLDER,'app/data/prereq_excel/currencies.xlsx')
EXCHANGE_RATE_DATA = os.path.join(THIS_FOLDER,'app/data/prereq_excel/exchange_rates.xlsx')
STOCKS_DATA = os.path.join(THIS_FOLDER,'app/data/prereq_excel/stocks.xlsx')

# Load data from Excel
participants_data = pd.read_excel(PARTICIPANTS_DATA)[ ['ID', 'Team', 'Password']]
news_data =pd.read_excel(NEWS_DATA)
currency_data = pd.read_excel(CURRENCY_DATA)
exchange_rate_data = pd.read_excel(EXCHANGE_RATE_DATA)
stocks_data = pd.read_excel(STOCKS_DATA)

# Export data to CSV for proper use
participants_data.to_csv( os.path.join(THIS_FOLDER,"app/data/prereq/participants.csv") )
news_data.to_csv( os.path.join(THIS_FOLDER,"app/data/prereq/news.csv") )
currency_data.to_csv( os.path.join(THIS_FOLDER,"app/data/prereq/currencies.csv") )
exchange_rate_data.to_csv( os.path.join(THIS_FOLDER,"app/data/prereq/exchange_rates.csv") )
stocks_data.to_csv( os.path.join(THIS_FOLDER,"app/data/prereq/stocks.csv") )


# Reset DB and start fresh or use existing one?
answer = None

if(os.path.exists(DATABASE)):
    print("Database already exists.")
    answer = input("Y to use it, N to delete and start fresh: ")
    if(answer == 'Y'):
        print("End of script")

    elif(answer == 'N'):
        print("Deleting existing database")
        os.remove(DATABASE)


if(answer=='N' or not os.path.exists(DATABASE)):
    print("----------")
    print("Initalising fresh database!")
    db = sqlite3.connect(DATABASE)
    # db.set_trace_callback(print)
    db.row_factory = sqlite3.Row
    c = db.cursor()

    c.execute("""
        CREATE TABLE `users` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            `team` TEXT, `password` TEXT
        );
        """)

    c.execute("""
        CREATE TABLE `config` (
        	`key`	TEXT,
        	`value`	INTEGER
        );
        """)

    c.execute("""
        CREATE TABLE `news` (
        	`round`	INTEGER NOT NULL,
        	`news_description` TEXT NOT NULL,
            `stock_affected` INTEGER NOT NULL,
            `perc_effect` REAL NOT NULL
        );
    """)

    c.execute("""
        CREATE TABLE `currency_portfolio` (
        	`user_id`	INTEGER NOT NULL,
        	`currency_id`	INTEGER NOT NULL,
        	`amount`	INTEGER NOT NULL
        );
    """)

    c.execute("""
        CREATE TABLE `transaction_log` (
        	`user_id`	INTEGER NOT NULL,
            `round`    INTEGER NOT NULL,
        	`market`	TEXT NOT NULL,
        	`action`	TEXT NOT NULL,
            `time` DATETIME DEFAULT (datetime('now','localtime'))
        );
    """)

    c.execute("""
        CREATE TABLE `stock_prices` (
        	`stockID`	INTEGER NOT NULL,
        	`opening_price`	REAL NOT NULL,
        	`current_price`	REAL NOT NULL
        );
    """)

    c.execute("""
        CREATE TABLE `stock_portfolio` (
        	`user_id`	INTEGER NOT NULL,
        	`stock_id`	INTEGER NOT NULL,
        	`qty`	INTEGER NOT NULL,
            `book_value`    REAL NOT NULL
        );
    """)

    print("[1] Created Tables")

    #### After database tables have been created,
    #### Fill database


    c.execute("""
        INSERT INTO config(key,value)
            VALUES
                ('current_round', 0),
                ('markets_open', 0);
    """)

    trs = 0

    for i in range(len(participants_data)): #loop over the rows
        c.execute("INSERT INTO users(team, password) VALUES(?, ?); ",  tuple( participants_data.iloc[i, 1:] ) )
        trs = participants_data.iloc[i, 0] % len(initial_portfolios)


        for j in range(len(currency_data)):
            c.execute("INSERT INTO currency_portfolio VALUES(?, ?, ?);", ( participants_data.iloc[i, 0], currency_data.iloc[j, 0], initial_portfolios[trs]['currencies'][currency_data.iloc[j, 0] ] ))

        for j in range(len(stocks_data)):
            qty = initial_portfolios[trs]['stocks'][ stocks_data.iloc[j, 0] ]
            c.execute("INSERT INTO stock_portfolio VALUES(?,?,?,?);", (participants_data.iloc[i, 0], stocks_data.iloc[j, 0], qty, stocks_data.iloc[j, 4] * qty) )

    for i in range(len(news_data)):
        c.execute("INSERT INTO news(round, news_description, stock_affected, perc_effect) VALUES(?,?, ?, ?);", tuple(news_data.iloc[i, 0:] ) )


    for i in range(len(stocks_data)):
        c.execute("INSERT INTO stock_prices(stockID, opening_price, current_price) VALUES(?,?,?);", (stocks_data.iloc[i, 0], stocks_data.iloc[i, 4], stocks_data.iloc[i, 4]))

    print("[2] Injected data")
    print("[3] Database successfully initialised!")
    print("---- E o S ----- ")
    db.commit()
    db.close()