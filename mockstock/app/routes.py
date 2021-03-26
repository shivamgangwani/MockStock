from app import app


import time, sqlite3
import pandas as pd
from math import ceil
from functools import wraps

from flask import render_template, request, redirect, url_for, flash, session, g, jsonify
from .forms import LoginForm, AdminLoginForm, ForexForm, StockForm_Full
from .database import get_db, GetMarketStatus, GetUserData, GetStockPrices
from .models import (currencies, ExchangeRate, exchange_rates_complex, NO_OF_ROUNDS,
                    currency_data, exchange_rates, stocks_data, stocks, ListOfStocks,
                    IsValidStockExchange, GetCurrencyLimitBand, GetProportionFromLimitBand,
                    Curr_ShortNameToID, Curr_ExchangeToID, stocks)
##################

from .app_config import (admin_name, admin_pass, MAX_ROUNDS, MIN_ROUNDS, confirmation_window)

#############################################
####### CUSTOM FUNCTIONS REQUIRED  ##########
#############################################


def IsUserLoggedIn():
    return ('user' in session)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(session.get('user', None)==None):
            flash("You must be logged in to view that page!", 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def IsUserAdmin():
    return session.get('admin', False)

def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(session.get('admin', False) == False):
            flash("You must be admin to view that page!", 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def CurrencyCommas(val):
    return "{:0,.2f}".format(val)


#############################################
################# ROUTES  ###################
#############################################
@app.context_processor
def utility_processor():
    return dict( currencies=currencies, stocks=stocks, confirmation_window=confirmation_window)


@app.route('/')
@app.route('/index')
def index():
    return render_template('landing.html')

@app.route('/market_status')
def market_status():
    return jsonify(GetMarketStatus())


@app.route('/login', methods=['POST', 'GET'])
def login():
    if(IsUserLoggedIn()):
        return redirect(url_for('dashboard'))
    else:
        form=LoginForm()
        if(request.method=='POST'):
            if form.validate_on_submit():

                db=get_db()
                c=db.cursor()
                c.execute("SELECT * FROM users WHERE team=?;", (form.team_name.data, ))
                result=c.fetchone()
                c.close()
                if(result == None): #row not found
                    flash('Invalid team!', 'error')
                    flash("Login credentials are CASE-SENSITIVE.", 'error')
                    return render_template('login.html', form=form)

                else:
                    if(form.password.data==result[2]):
                        session['user']={'id':result[0], 'team':result[1]}
                        flash('Logged in successfully!', 'success')
                        return redirect(url_for('dashboard'))

                    else:
                        flash('Invalid password!', 'error')
                        flash("Login credentials are CASE-SENSITIVE.", 'error')
                        return render_template('login.html', form=form)
            else:
                flash('Please fill the form correctly', 'error')
                return render_template('login.html', form=form)
        else:
            return render_template('login.html', form=form)


#Basic navigation routes
@app.route('/dashboard')
@login_required
def dashboard():
#    if(not IsUserLoggedIn()):
#        return redirect(url_for('login'))
    session['portfolio']=GetUserData(session['user']['id'])
    return render_template('dashboard.html', prices=GetStockPrices()  )


@app.route('/logout')
def logout():
    if(IsUserLoggedIn() ):
        flash('Logged out.', 'notification')
        session.pop('user', None)
    else:
        flash("Not logged in, can't log out!", 'error')
    return redirect(url_for('login'))


@app.route('/transaction_log/limit=<int:limit>')
@login_required
def transaction_log(limit=30):
    db=get_db()
    c=db.cursor()
    if(limit<=0):
        c.execute("SELECT strftime('%H:%M:%S', time),market,action FROM transaction_log WHERE user_id=? ORDER BY time DESC;", (session['user']['id'], ) )
    elif(limit>0):
        c.execute("SELECT strftime('%H:%M:%S', time),market,action FROM transaction_log WHERE user_id=? ORDER BY time DESC LIMIT ?;", (session['user']['id'], limit) )
    result=c.fetchall()
    c.close()
    return render_template('transaction_log.html',  team=session['user']['team'], transaction_data=result, limit=limit)



@app.route('/markets')
@login_required
def market_portal():
    return render_template('markets.html', currency_data=currencies, mkt_status=GetMarketStatus() )


@app.route('/news')
@login_required
def news():
    db=get_db()
    c=db.cursor()
    c.execute("SELECT * FROM news WHERE round=?;", (GetMarketStatus()['current_round'], ) )
    result=c.fetchall()
    c.close()
    return render_template('news.html', news=result)

#MARKETS
#Note: When rendering order_confirmation view, add check to ensure
#That the session contains 'order' dict information, if not then redirect asap
#Pop this out when order gets cancelled

@app.route('/markets/<mkt>', methods=['POST', 'GET'])
@login_required
def market_view(mkt):
    mkt_data= GetMarketStatus()
    if(mkt_data['markets_open'] == 0):
        flash("Markets are closed!", 'notification')
        return redirect(url_for('market_portal'))

    if(request.method=='POST'):
        if(IsValidStockExchange(mkt)):
            form=StockForm_Full()
            if not form.validate_on_submit():
                flash("Please fill the form correctly!",'error')

                print("---------------------------")
                print("Stock form could not be validated")
                print(session['user'])
                print(form.data)
                print(form.errors)
                print("---------------------------")
                return redirect(url_for('market_portal'))

            else: #form validated
                c_round=mkt_data['current_round']
                try:
                    form.round.data=int(form.round.data)
                    form.started_at.data=int(form.started_at.data)
                except Exception as e:
                    flash("Please don't mess with the code!", 'error')
                    flash("You will be disqualified!", 'error')
                    print("---------------------------")
                    print("Form hidden fields manipulated!")
                    print(session['user'])
                    print(e)
                    print("---------------------------")
                    return redirect(url_for('dashboard'))

                if( form.round.data != hash( c_round ) ):
                    flash("A new round has started. Please place your order again!", 'error')
                    return redirect(url_for('dashboard'))

                else:
                    if('order_details' not in session):
                        flash("Transaction data missing/has been tampered with. ", 'error')
                        flash("This can happen if you press back after completing a transaction, or ", 'error')
                        flash("Do not play with cookies!", 'error')
                        flash("Attempt all transactions only in one tab! ", 'error')
                        print("---------------------------")
                        print("Transaction Tamper Error - STOCKS!")
                        print(session['user'])
                        print("---------------------------")
                        return redirect(url_for('market_portal'))

                    else:
                        if( (form.started_at.data != hash(session['order_details']['started_at'] ))  or (mkt != session['order_details']['market'] ) ):
                            flash("Please do not initiate multiple transactions at once! ", 'error')
                            flash("Only the latest transaction initiated will be carried out!", 'error')
                            print("---------------------------")
                            print("Multiple Transactions Error!")
                            print("NOTE: started_at & mkt do not match!")
                            print(session['user'])
                            print("---------------------------")
                            return redirect(url_for('dashboard'))
                        else:
                            order_data=form.stox.data
                            session['order_details']['order_specifics'] = order_data
                            which_stocks = ListOfStocks(mkt)
                            which_curr = Curr_ExchangeToID(mkt)
                            prices = GetStockPrices()


                            if(GetUserData(session['user']['id']) != session['portfolio']):
                                flash("Please do not attempt to do multiple transactions at once!", 'error')
                                print("---------------------------")
                                print("Multiple Transactions Error!")
                                print("NOTE: session portfolio and transaction portfolio do not match!")
                                print(session['user'])
                                print("---------------------------")
                                session.pop('order_details', None)
                                return redirect(url_for('market_portal'))

                            else:
                                price_change=False
                                for i in range (len(which_stocks)):
                                    if(session['order_details']['prices'][which_stocks[i].id]['current_price'] != prices[ which_stocks[i].id ]['current_price'] and order_data[i]['qty'] != 0):
                                        price_change=True
                                        break

                                if(price_change==True):
                                    flash("Prices have changed", 'notification')
                                    return redirect(url_for('confirm_order'))

                                else:
                                    order_valid=False #check if any qty>0
                                    amt_spent=0
                                    for i in range(len(which_stocks)):
                                        if(order_data[i]['qty'] != 0):
                                            order_valid=True
                                            if(order_data[i]['option']==0): #buy
                                                amt_spent += order_data[i]['qty']* prices[ which_stocks[i].id ]['current_price']
                                            elif(order_data[i]['option']==1): #sell
                                                if(session['portfolio']['stock_holding'][ which_stocks[i].id ]['qty'] >= order_data[i]['qty'] ):
                                                    amt_spent -= order_data[i]['qty']*prices[ which_stocks[i].id]['current_price']
                                                else:
                                                    flash("You are trying to sell more than you have!", 'error')
                                                    flash("Stock: "+ which_stocks[i].name, 'error' )
                                                    flash("Amount held: "+str(session['portfolio']['stock_holding'][ which_stocks[i].id]['qty'] ), 'error')
                                                    flash("Amount you tried to sell: "+str(order_data[i]['qty'] ) , 'error')
                                                    session.pop('order_details', None)
                                                    return redirect(url_for('market_portal'))

                                    if(not order_valid):
                                        flash("You entered 0 quantity for all stocks!", 'notification')
                                        session.pop('order_details', None)
                                        return redirect(url_for('market_portal'))

                                    else:
                                        if(amt_spent > session['portfolio']['currency_holding'][which_curr] ):
                                            flash("Insufficient funds!", 'error')
                                            flash("You have: "+str(session['portfolio']['currency_holding'][which_curr]), 'error')
                                            flash("You are trying to spend: "+str(amt_spent), 'error')
                                            session.pop('order_details', None)
                                            return redirect(url_for('market_portal'))
                                        else:
                                            try:
                                                flash('Order successfully proccessed!', 'success')
                                                db=get_db()
                                                c=db.cursor()
                                                c.execute("UPDATE currency_portfolio SET amount=amount-? WHERE user_id=? AND currency_id=?;", (amt_spent, session['user']['id'], which_curr))
                                                for i in range(len(which_stocks)):
                                                    proportion = GetProportionFromLimitBand( GetCurrencyLimitBand(which_curr, prices[ which_stocks[i].id ]['current_price']*order_data[i]['qty'] ))
                                                    if(order_data[i]['qty'] != 0):
                                                        if(order_data[i]['option']==0):
                                                            c.execute("UPDATE stock_portfolio SET qty=qty+?, book_value=book_value+? WHERE stock_id=? AND user_id=?;", (order_data[i]['qty'], prices[ which_stocks[i].id ]['current_price']*order_data[i]['qty'], which_stocks[i].id, session['user']['id']  ))
                                                            trans="Bought {} units of {} at rate of {} {}".format( order_data[i]['qty'], which_stocks[i].name, currencies[which_curr].short_name ,prices[ which_stocks[i].id]['current_price'] )
                                                            flash(trans, 'success')
                                                            c.execute("INSERT INTO transaction_log(user_id, round, market, action) VALUES(?, ?, ?, ?);", (session['user']['id'],c_round, mkt, trans) )
                                                            c.execute("UPDATE stock_prices SET current_price=ROUND(current_price*?, 2) WHERE stockID=?;", (1+proportion, which_stocks[i].id ) )
                                                        else:
                                                            c.execute("UPDATE stock_portfolio SET qty=qty-?, book_value=book_value-? WHERE stock_id=? AND user_id=?;", (order_data[i]['qty'], (order_data[i]['qty']/session['portfolio']['stock_holding'][which_stocks[i].id ]['qty'])*session['portfolio']['stock_holding'][ which_stocks[i].id ]['book_value'], which_stocks[i].id, session['user']['id']  ))
                                                            trans="Sold {} units of {} at rate of {} {}".format( order_data[i]['qty'], which_stocks[i].name, currencies[which_curr].short_name ,prices[ which_stocks[i].id]['current_price'] )
                                                            flash(trans, 'success')
                                                            c.execute("INSERT INTO transaction_log(user_id, round, market, action) VALUES(?, ?, ?, ?);", (session['user']['id'],c_round, mkt, trans) )
                                                            c.execute("UPDATE stock_prices SET current_price=ROUND(current_price*?, 2) WHERE stockID=?;", (1-proportion, which_stocks[i].id ) )
                                                db.commit()


                                            except sqlite3.Error as error:
                                                print("Error while connecting to sqlite \n", error)
                                                flash("A problem occured. Contact event administrator immediately!", 'error')
                                                print("---------------------------")
                                                print("Stock Form Normal SQL error occured!")
                                                print(session['user'])
                                                print(error)
                                                print(order_data)
                                                print("---------------------------")

                                            finally:
                                                session.pop('order_details', None)
                                                return redirect(url_for('dashboard'))


        elif(mkt=='FOREX'):
            form = ForexForm( )

            if not form.validate_on_submit():
                flash("Please fill the form correctly!",'error')
                print("---------------------------")
                print("Forex form could not be validated")
                print(session['user'])
                print(form.data)
                print(form.errors)
                print("---------------------------")

                for fieldName, errorMessages in form.errors.items():
                    flash(fieldName+": "+str(errorMessages), 'error')
                return redirect(url_for('market_view', mkt=mkt))

            else:
                c_round=mkt_data['current_round']
                try:
                    form.round.data=int(form.round.data)
                    form.started_at.data=int(form.started_at.data)
                except Exception as e:
                    flash("Please don't mess with the code!", 'error')
                    flash("You will be disqualified!", 'error')
                    print("---------------------------")
                    print("Form hidden fields manipulated!")
                    print(session['user'])
                    print(e)
                    print("---------------------------")
                    return redirect(url_for('dashboard'))

                if( form.round.data != hash( c_round ) ):
                    flash("A new round has started. Please place your order again!", 'error')
                    return redirect(url_for('market_portal'))

                else:
                    if('order_details' not in session):
                        flash("Transaction data missing/has been tampered with. ", 'error')
                        flash("This can happen if you press back after completing a transaction, or ", 'error')
                        flash("Do not play with cookies!", 'error')
                        flash("Attempt all transactions only in one tab! ", 'error')
                        print("---------------------------")
                        print("Transaction Tamper Error - FOREX!")
                        print(session['user'])
                        print("---------------------------")
                        return redirect(url_for('market_portal'))

                    else:
                        if( (form.started_at.data != hash(session['order_details']['started_at'] ))  or (mkt != session['order_details']['market'] ) ):
                            flash("Please do not initiate multiple transactions at once! ", 'error')
                            flash("Only the latest transaction initiated will be carried out!", 'error')
                            print("---------------------------")
                            print("Multiple Transactions Error!")
                            print("NOTE: started_at & mkt do not match!")
                            print(session['user'])
                            print("---------------------------")
                            return redirect(url_for('dashboard'))
                        else:

                            a=form.from_currency.data
                            b=form.to_currency.data
                            amt=round(form.amount.data, 3)
                            d=ExchangeRate(c_round, a,b)

                            portfolio = GetUserData(session['user']['id'])
                            if(portfolio != session['portfolio']):
                                flash("Please do not attempt to do multiple transactions at once!", 'error')
                                print("---------------------------")
                                print("Multiple Transactions Error!")
                                print("NOTE: session portfolio and transaction portfolio do not match!")
                                print(session['user'])
                                print("---------------------------")
                                session.pop('order_details', None)
                                return redirect(url_for('market_portal'))
                            else:

                                a_ = portfolio['currency_holding'][a]
                                if(amt > a_):
                                    flash("Insufficient funds!", 'error')
                                    return redirect(url_for('market_portal'))
                                else:
                                    try:
                                        db=get_db()
                                        c=db.cursor()
                                        c.execute("UPDATE currency_portfolio SET amount=amount-? WHERE user_id=? AND currency_id=?;", (round(amt, 4), session['user']['id'], a))
                                        c.execute("UPDATE currency_portfolio SET amount=amount+? WHERE user_id=? AND currency_id=?;", (round(d*amt, 4), session['user']['id'], b))
                                        trans = "Bought {} {} and Sold {} {} at rate of {}".format(currencies[b].short_name, CurrencyCommas(round(d*amt, 4)), currencies[a].short_name, CurrencyCommas( round(amt, 4) ), round(d, 5))
                                        c.execute("INSERT INTO transaction_log(user_id, round, market, action) VALUES(?, ?, ?, ?);", (session['user']['id'],c_round, mkt, trans))
                                        db.commit()

                                        flash("Order successfully processed", 'success')
                                        flash("Bought: {} {}".format(currencies[b].short_name, CurrencyCommas(d*amt) ), 'success')
                                        flash("Sold: {} {}".format(currencies[a].short_name, CurrencyCommas(amt) ), 'success')
                                        flash("Exchange rate: {}".format( round(d, 5) ), 'success')

                                    except sqlite3.Error as error:
                                        print("Error while connecting to sqlite \n", error)
                                        flash("A problem occured. Contact event administrator immediately!", 'error')
                                        print("---------------------------")
                                        print("Forex Form Normal SQL error occured!")
                                        print(session['user'])
                                        print(error)
                                        print(order_data)
                                        print("---------------------------")

                                    finally:
                                        session.pop('order_details', None)
                                        return redirect(url_for('dashboard'))



        else:
            flash('Invalid market: '+mkt, 'error')
            flash('Contact event adminstrators immediately!', 'error')
            return render_template('dashboard.html')


    elif(request.method == 'GET'):
        if('order_details' in session):
            flash(f"Your incomplete/ongoing transaction before this in the {session['order_details']['market']} will not be processed since you have started a new transaction.", 'notification')
            session.pop('order_details', None)

        started_at = time.time()
        c_round= mkt_data['current_round']

        session['order_details']= {
            'started_at':started_at,
            'in_round':c_round,
            'market':mkt,
            'portfolio': GetUserData(session['user']['id'])
        }

        #Market specific shit:
        if(IsValidStockExchange(mkt)):
            which_stocks = ListOfStocks(mkt)
            which_curr = Curr_ExchangeToID(mkt)
            prices = GetStockPrices()
            session['order_details']['prices'] = prices
            form = StockForm_Full(round=hash(c_round), started_at=hash(started_at) )
            return render_template('orders/order.html', mkt=mkt, form=form, stonks=which_stocks, stonk_ids=[i.id for i in which_stocks], curr=which_curr, curr_name=currencies[which_curr].short_name , prices=prices )

        else:
            form = ForexForm(round=hash(c_round), started_at=hash(started_at ) ) #pass hidden fields
            return render_template('orders/order_forex.html', mkt=mkt, form=form, exchange_rates=exchange_rates_complex[ c_round ] )


@app.route('/confirm_order', methods=['POST', 'GET'] )
@login_required
def confirm_order():
    if(GetUserData(session['user']['id']) != session['portfolio'] ):
        return redirect(url_for('cancel_order', reason='portfolio_change'))

    else:
        if(request.method=='GET'):
            if('order_details' not in session):
                flash("Transaction data missing/has been tampered with. ", 'error')
                flash("This can happen if you press back after completing a transaction, or ", 'error')
                flash("Do not play with cookies!", 'error')
                flash("Attempt all transactions only in one tab! ", 'error')
                print("---------------------------")
                print("Transaction Tamper Error - STOCKS_PCHANGE_VERSION!")
                print(session['user'])
                print("---------------------------")
                return redirect(url_for('market_portal'))
            else:
                order_details = session['order_details']
                mkt=order_details['market']
                order_data = order_details['order_specifics']
                old_order_data = order_data
                which_stocks = ListOfStocks(mkt)
                which_curr = Curr_ExchangeToID(mkt)

                old_prices = order_details['prices']
                prices = GetStockPrices()
                session['order_details']['new_prices'] = prices

                amt_spent=0
                new_amt_spent=0
                affordability_status=0
                qty_bought=0
                #0 -> affordable
                #1 -> unaffordable
                #2 -> affordable with certain changes

                for i in range(len(which_stocks)):
                    if(order_data[i]['qty'] != 0):
                        if(order_data[i]['option']==0): #buy
                            amt_spent += order_data[i]['qty']* prices[ which_stocks[i].id ]['current_price']
                            qty_bought+=order_data[i]['qty']

                        elif(order_data[i]['option']==1): #sell
                            if(session['portfolio']['stock_holding'][ which_stocks[i].id ]['qty'] >= order_data[i]['qty'] ):
                                amt_spent -= order_data[i]['qty']*prices[ which_stocks[i].id]['current_price']
                            else:
                                flash("You are trying to sell more than you have!", 'error')
                                flash(f"Stock: {which_stocks[i].name}", 'error' )
                                flash(f"Amount held: {session['portfolio']['stock_holding'][ which_stocks[i].id]['qty']}", 'error')
                                flash(f"Amount you tried to sell: {order_data[i]['qty']}", 'error')
                                session.pop('order_details', None)
                                return redirect(url_for('market_portal'))

                if(amt_spent <= session['portfolio']['currency_holding'][which_curr]):
                    affordability_status=0
                    new_amt_spent=amt_spent
                elif(amt_spent > session['portfolio']['currency_holding'][which_curr] ):
                    new_amt_spent=0
                    deficit = amt_spent - session['portfolio']['currency_holding'][which_curr]
                    for i in range(len(which_stocks)):
                        if(order_data[i]['qty'] != 0):
                            if( order_data[i]['option']==0):
                                order_data[i]['qty'] -= ceil( ( (order_data[i]['qty']/qty_bought)*(deficit) )/ prices[ which_stocks[i].id]['current_price'] )
                                new_amt_spent+=order_data[i]['qty']*prices[ which_stocks[i].id ]['current_price']
                            elif(order_data[i]['option']==1):
                                new_amt_spent-=order_data[i]['qty']*prices[ which_stocks[i].id ]['current_price']

                    session['order_details']['order_specifics'] = order_data
                    if(new_amt_spent > session['portfolio']['currency_holding'][which_curr]):
                        #this should not happen
                        flash("A problem occured. Contact event administrator!", 'error')
                        flash("Error: Portfolio reallocation failed.", 'error')
                        print("---------------------------")
                        print("Stock Order Confirmation Error - Portfolio Reallocation Failed!")
                        print(session['user'])
                        print(session['order_details'])
                        print("---------------------------")
                        affordability_status=1
                        return redirect(url_for('dashboard'))
                    else:
                        affordability_status=2

                if(affordability_status == 0 or affordability_status==2):
                    session['order_details']['confirmation_started'] = time.time()
                    return render_template('orders/order_confirmation.html', stonx=which_stocks, old_prices=old_prices, new_prices=prices, which_curr=which_curr, curr_name=currencies[which_curr].short_name, affordable=affordability_status, old_order=old_order_data, new_order=session['order_details']['order_specifics'], total_exp=new_amt_spent)

@app.route('/complete_order')
@login_required
def complete_order():
    if('order_details' not in session):
        flash("Transaction data missing/has been tampered with. ", 'error')
        flash("This can happen if you press back after completing a transaction", 'error')
        flash("Do not play with cookies!", 'error')
        flash("Attempt all transactions only in one tab! ", 'error')
        return redirect(url_for('market_portal'))

    else:
        if(GetUserData(session['user']['id']) != session['portfolio'] ):
            return redirect(url_for('cancel_order', reason='portfolio_change'))
        mkt_status=GetMarketStatus()
        order_details=session['order_details']
        order_data = session['order_details']['order_specifics']
        mkt=order_details['market']
        c_round=order_details['in_round']
        which_curr=Curr_ExchangeToID(mkt)
        which_stocks=ListOfStocks(mkt)
        prices=order_details['new_prices']

        if(mkt_status['markets_open'] == 0):
            flash("Markets are closed!", 'notification')
            return redirect(url_for('market_portal'))

        else:
            if(order_details['in_round'] != c_round ):
                flash("A new round has started. Please place your order again!", 'error')
                return redirect(url_for('market_portal'))
            else:
                if( time.time() - session['order_details']['confirmation_started'] > confirmation_window):
                    return redirect(url_for('cancel_order', reason='timer'))
                amt_spent=0
                for i in range(len(which_stocks)):
                    if(order_data[i]['qty'] != 0):
                        if(order_data[i]['option']==0): #buy
                            amt_spent += order_data[i]['qty']* prices[ which_stocks[i].id ]['current_price']
                        elif(order_data[i]['option']==1): #sell
                            if(session['portfolio']['stock_holding'][ which_stocks[i].id ]['qty'] >= order_data[i]['qty'] ):
                                amt_spent -= order_data[i]['qty']*prices[ which_stocks[i].id]['current_price']
                            else:
                                flash("You are trying to sell more than you have!", 'error')
                                flash(f"Stock: {which_stocks[i].name}", 'error' )
                                flash(f"Amount held: {session['portfolio']['stock_holding'][ which_stocks[i].id]['qty']}", 'error')
                                flash(f"Amount you tried to sell: {order_data[i]['qty']}" , 'error')
                                session.pop('order_details', None)
                                return redirect(url_for('market_portal'))

                if(amt_spent > session['portfolio']['currency_holding'][which_curr] ):
                        flash("Insufficient funds!", 'error')
                        flash(f"You have: {session['portfolio']['currency_holding'][which_curr]}", 'error')
                        flash(f"You are trying to spend: {amt_spent}", 'error')
                        session.pop('order_details', None)
                        return redirect(url_for('market_portal'))
                else:
                    try:
                        flash('Order successfully proccessed!', 'success')
                        db=get_db()
                        c=db.cursor()
                        c.execute("UPDATE currency_portfolio SET amount=amount-? WHERE user_id=? AND currency_id=?;", (amt_spent, session['user']['id'], which_curr))
                        for i in range(len(which_stocks)):
                            proportion = GetProportionFromLimitBand( GetCurrencyLimitBand(which_curr, prices[ which_stocks[i].id ]['current_price']*order_data[i]['qty'] ))
                            if(order_data[i]['qty'] != 0):
                                if(order_data[i]['option']==0):
                                    c.execute("UPDATE stock_portfolio SET qty=qty+?, book_value=book_value+? WHERE stock_id=? AND user_id=?;", (order_data[i]['qty'], prices[ which_stocks[i].id ]['current_price']*order_data[i]['qty'], which_stocks[i].id, session['user']['id']  ))
                                    trans="Bought {} units of {} at rate of {} {}".format( order_data[i]['qty'], which_stocks[i].name, currencies[which_curr].short_name ,prices[ which_stocks[i].id]['current_price'] )
                                    flash(trans, 'success')
                                    c.execute("INSERT INTO transaction_log(user_id, round, market, action) VALUES(?, ?, ?, ?);", (session['user']['id'],c_round, mkt, trans) )
                                    c.execute("UPDATE stock_prices SET current_price=ROUND(current_price*?, 2) WHERE stockID=?;", (1+proportion, which_stocks[i].id ) )
                                else:
                                    c.execute("UPDATE stock_portfolio SET qty=qty-?, book_value=book_value-? WHERE stock_id=? AND user_id=?;", (order_data[i]['qty'], (order_data[i]['qty']/session['portfolio']['stock_holding'][which_stocks[i].id ]['qty'])*session['portfolio']['stock_holding'][ which_stocks[i].id ]['book_value'], which_stocks[i].id, session['user']['id']  ))
                                    trans="Sold {} units of {} at rate of {} {}".format( order_data[i]['qty'], which_stocks[i].name, currencies[which_curr].short_name ,prices[ which_stocks[i].id]['current_price'] )
                                    flash(trans, 'success')
                                    c.execute("INSERT INTO transaction_log(user_id, round, market, action) VALUES(?, ?, ?, ?);", (session['user']['id'],c_round, mkt, trans) )
                                    c.execute("UPDATE stock_prices SET current_price=ROUND(current_price*?, 2) WHERE stockID=?;", (1-proportion, which_stocks[i].id ) )
                        db.commit()
                        session.pop('order_details', None)
                        return redirect(url_for('dashboard'))

                    except sqlite3.Error as error:
                        print("Error while connecting to sqlite \n", error)
                        flash("A problem occured. Contact event administrator immediately!", 'error')
                        print("---------------------------")
                        print("Forex Form Normal SQL error occured!")
                        print(session['user'])
                        print(error)
                        print(order_data)
                        print("---------------------------")

@app.route('/cancel_order/<reason>')
@login_required
def cancel_order(reason):
    session.pop('order_details', None)
    if(reason=='cancel'):
        flash('Order cancelled.', 'notification')
    elif(reason=='timer'):
        flash('Order cancelled as you did not confirm in time!', 'error')
    elif(reason=='portfolio_change'):
        flash("Order terminated as you attempted to perform multiple transactions simultaneously!", 'error')
    return redirect(url_for('dashboard'))


###### HIDDEN VIEWS, ONLY TO ACCESS DATA !!!!!! #######
@app.route('/user_data')
def user_data_view():
    if('user' in session):
        session['portfolio']=GetUserData(session['user']['id'] )
        return jsonify(dict(session) )
    else:
        return redirect(url_for('dashboard'))

##############################################################################################################
##############################################################################################################
############################################ADMIN ROUTES######################################################
##############################################################################################################
##############################################################################################################

@app.route('/admin_area')
@admin_only
def admin_area():
    return render_template('admin/admin.html', mkt_status=GetMarketStatus() )

@app.route('/admin_login', methods=['POST', 'GET'])
def admin_login():
    if(IsUserAdmin()):
        return redirect(url_for('admin_area'))
    else:
        form=AdminLoginForm()
        if(request.method=='POST'):
            if(form.user.data==admin_name and form.password.data==admin_pass):
                session['admin']=True
                return redirect(url_for('admin_area'))
            else:
                session['admin']=False
                print(form.user.data, form.password.data)
                return render_template('admin/admin_login.html', form=form)
        return render_template('admin/admin_login.html', form=form)


@app.route('/admin/mkt_bool')
@admin_only
def switch_market_status():
    result=GetMarketStatus()
    db=get_db()
    c=db.cursor()
    c.execute("UPDATE config SET value=? WHERE key='markets_open'; ", (int(not result['markets_open']), ) )
    db.commit()
    c.close()
    return redirect(url_for('admin_area'))


@app.route('/admin/round_change/<what>')
@admin_only
def change_round(what):
    mkt_status = GetMarketStatus()
    if(mkt_status['markets_open'] == 1):
        flash("Please close the market before changing rounds!", 'error')
        return redirect(url_for('admin_area'))
    next_round=mkt_status['current_round']
    db=get_db()
    c=db.cursor()
    if(what=='next'):
        next_round+=1
        if(next_round>=NO_OF_ROUNDS):
            flash("News & exchange rates only specified for {} rounds! ".format(NO_OF_ROUNDS), 'error')
            return redirect(url_for('admin_area'))

            #update prices
        try:
            c.execute("SELECT * FROM news WHERE round=?;", (next_round-1, ))
            result = c.fetchall()
            for i in result:
                c.execute("UPDATE stock_prices SET current_price=ROUND(current_price*?, 2) WHERE stockID=?;", ( 1+ (i[3]/100), i[2] ) )

        except Exception as e:
            flash("Error occured: Could not update prices due to news when changing rounds!", 'error')
            flash(e, 'error')
            print(e)
            return redirect(url_for('admin_area'))

    elif(what=='prev'):
        if(next_round==0):
            flash("Rounds must vary from 0 to n!", 'error')
            return redirect(url_for('admin_area'))
        next_round-=1
        if(next_round!=0):
            flash("Note that price changes due to news are not reversed when going back rounds!", 'notification')
            flash("For that, go back to round 0 and reset prices!", 'notification')
        elif(next_round==0):
            try:
                c.execute("UPDATE stock_prices SET current_price=opening_price;")
                flash("Prices set back to opening_price", 'notification')
            except Exception as e:
                print(e)
                flash("Error occured: could not reset prices when moving back to round 0!", 'error')
                return redirect(url_for('admin_area'))

    try:
        c.execute("UPDATE config SET value=? WHERE key='current_round';", (next_round,))
        db.commit()
        c.close()
    except:
        flash("Error occured: Could not change round!", 'error')
        return redirect(url_for('admin_area'))

    if( (next_round >= MAX_ROUNDS) or (next_round not in exchange_rates_complex) ):
        flash("Foreign exchange data for this round does not exist.", 'notification')
        flash("Highest round values will be used instead.", 'notification')

    return redirect(url_for('admin_area'))

@app.route('/admin/export_results')
@admin_only
def admin_export_result():
    mkt_status=GetMarketStatus()
    if(mkt_status['markets_open']==True):
        flash("Close the market before exporting results!", 'error')
        return redirect(url_for('admin_area'))
    else:
        try:
            print("---- EXPORTING RESULTS ------")
            db=get_db()
            c=db.cursor()
            c.execute("SELECT * FROM stock_prices;")
            stock_prices={}
            result=c.fetchall()
            print('----- stock prices ------ ')
            for i in result:
                print(i[0], i[1], i[2] )
                stock_prices[ i[0] ] = i[2]

            c.execute("SELECT * FROM users;")
            result = c.fetchall()
            teams={}
            for i in result:
                teams[ i[0] ] = i[1]

            stock_portfolios={}
            currency_portfolios={}

            # Everything converted to INR to calculate final scores
            base_curr = Curr_ShortNameToID("INR")

            for i in teams:
                c.execute("SELECT stock_id, qty FROM stock_portfolio WHERE user_id=?;", (i, ))
                stock_portfolios[i] = c.fetchall()

                c.execute("SELECT currency_id, amount FROM currency_portfolio WHERE user_id=?;", (i, ))
                currency_portfolios[i] = c.fetchall()

            net_worth={}
            curr_roundz = GetMarketStatus()['current_round']
            for i in teams:
                score=0
                print("-------------")
                print("Calculating score for {}".format(i) )
                net_worth[i] = 0
                for j in currency_portfolios[i]:
                    exch_rate = ExchangeRate( curr_roundz, j[0], base_curr)
                    net_worth[i] += j[1]*exch_rate
                    print("{} {} converted to INR at rate of {} = {}".format(j[1], currencies[ j[0] ].short_name, exch_rate, j[1]*exch_rate))
                    score += j[1]*exch_rate

                for m in stock_portfolios[i]:
                    exch_rate = ExchangeRate( curr_roundz, stocks[ m[0] ].currency, base_curr )
                    net_worth[i] += (m[1]*stock_prices[ m[0] ]) * exch_rate
                    print("{} {} at {} {} converted to INR at rate of {} = {}".format(m[1], stocks[ m[0] ].name, currencies[ stocks[ m[0] ].currency ].short_name, stock_prices[ m[0 ] ], exch_rate, m[1]*stock_prices[ m[0]]*exch_rate ))
                    score += m[1]*stock_prices[ m[0]]*exch_rate
                print("Score: {}, Net worth: {} ".format(score, net_worth[i] ))

            results = {}
            for i in teams:
                results[i] = {"team": teams[i], "score":net_worth[i]}

            unsorted = pd.DataFrame.from_dict(results, orient='index')
            arranged = unsorted.sort_values(['score'], ascending=False)
            return arranged.to_html(classes='u-full-width', float_format=lambda x: '%0.10f' % x)

        except Exception as e:
            flash("An error occured :(", 'error')
            flash(e, 'error')
            print(e)
            return redirect(url_for('admin_area'))


@app.route('/admin_logout')
def admin_logout():
    if('admin' in session):
        session.pop('admin')
    return redirect(url_for('index'))


@app.route('/admin/db/<view>')
@admin_only
def admin_views(view):
    db=get_db()
    table='none'
    result, col_names = list(), list()
    views_tables={
        #view_name: table_name
        'user_data': 'users',
        'transaction_data': 'transaction_log',
        'currency_portfolio_data': 'currency_portfolio',
        'news_data':'news',
        'portfolio_data':'stock_portfolio',
        'stock_prices_data':'stock_prices'
    }
    table = views_tables.get(view, 'none')
    if(table != 'none'):
        c=db.cursor()
        c.execute("SELECT * FROM {};".format(table) ) #DO NOT DO THIS NORMALLY
        col_names = [ i[0] for i in c.description ]
        result=c.fetchall()
        c.close()
    return render_template('admin/admin_views.html', view=view, data=result, col_names=col_names)


@app.route('/admin/excel/<view>')
@admin_only
def admin_views_excel(view):
    result=pd.DataFrame()
    views_frames={
        'currency_info':currency_data,
        'exchange_rates_info': exchange_rates,
        'stock_info': stocks_data
    }
    result = views_frames.get(view, pd.DataFrame() )
    result = result.to_html(classes='u-full-width', border=0)
    return render_template('admin/admin_views_excel.html', data=result, view=view)

@app.route('/admin/data_portal')
@admin_only
def admin_view_portal():
        return render_template('admin/view_portal.html')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()