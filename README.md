# Mock Stock 
This is a web application that was designed to organize a "mock stock" - a stock market simulation - for a college event.  

I built this at a time when I was learning Python & Flask, and as a result, the code does not follow best practices and is not very well documented. However, with the description below, it should be possible to make sense of how it works and how it can be adapted for your own use.

## Introduction
This is essentially a very simple CRUD application that was built to be hosted over a local area network to be used by 30-50 users at a time. Due to the scale of the event, there was no need for a proper registration system. Instead, all relevant data (users, stocks, currencies, exchange rates, news) is stored in Excel files beforehand, converted to .csv or SQL format before launching the website, and used from there while the website is up.

## Prerequisites
In the app/data/prereq_excel folder, there are 5 Excel files. This is where all information regarding the simulation must be stored first. The sample information should enable you to get started immediately as the data is pretty self-explanatory. Once this is done, you should run the initialise_database.py which will convert the information in the Excel files to a format that's faster to access while the website is up and running.

## Configuration
- app/app_config.py contains some variables that you can change depending on your use case. 
- - admin_name and admin_pass are the credentials to be used for logging into the admin area. Defaults are 'admin' and 'password', respectively
- - confirmation_window: if the price changes while a user is placing an order, the user is redirected to a 'confirm order' page where the user's order details are adjusted to the new price, and the new price is locked in for the duration of confirmation_window seconds. Even if the price changes more during this time, the user is allowed to buy/sell at the price that is specified on screen. I've kept this value at 30 seconds.
- g_config.py contains the config that I used when hosting the website on my local machine with gunicorn. With the specified configuration, I was able to smoothly host the web application on my local machine and WLAN with almost 30-50 active users for a few hours.

## Price Change Mechanism
In the simulation, prices can change due to 2 reasons:
- News: For this, refer to app/data/prereq_excel/news.xlsx
- Market: Through the buying/selling of stocks. For this, each currency has 3 'slabs', uplim_1, uplim_2, uplim_3, as specified in app/data/prereq_excel/currencies.xlsx. When a stock order exceeds a slab amount, a price change is triggered. By default, uplim_1 triggers a 2.5% change, uplim_2 triggers a 5% change, and uplim_3 triggers a 7.5% change. This is specified in the BandProportions dictionary in app/models.py, with no change corresponding to key -1, uplim_1 slab corresponding to key 0, and so on, and key -1 corresponding to 0% change, key 0 corresponding to 2.5% change and so on. The slab amounts as well as the percentage change can be adjusted - in fact, I strongly recommend it as the current system allows users to mindlessly exploit a strategy that forces the stock prices to oscillate, allowing these users to win the game without any effort.

## Result Calculation
For the final scores, all stock and currency holdings are converted to base_curr (by default, set to INR) and aggregated to arrive at final scores. 

## Admin
Admin area can be accessed through the url /admin_login with the credentials specified in app/app_config.py. All data can be viewed through the admin portal. Rounds can be switched around (markets must be closed when a round is changed) - note that going 'back' a round does not undo the price changes, unless you go back to round 0, in which case all prices are reset to the opening price.

## Demo Video
[Here's a demo video showing how the web application looks and works](https://youtu.be/evsqlguMPw4)

## Credits
I've used the Skeleton framework for CSS, and the stock market images were obtained from Google.
