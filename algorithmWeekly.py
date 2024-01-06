import pandas as pd
import os
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
from zipline import run_algorithm
from zipline.api import symbols, order_target_percent, order_value, get_open_orders
import warnings
warnings.filterwarnings("ignore")
from zipline.utils.calendar_utils import get_calendar
import json 
import numpy as np

f = open('./BacktestingData/mydata.json')
ticketToName = json.load(f)
# print(ticketToName) 

# Define the bundle registration and ingest function
csv_directory = './Data'  # Update this path
register(
    'my_custom_bundle',
    csvdir_equities(
        ['daily'],
        csv_directory,
    ),
    calendar_name='XBOM'
)

# Define the trading algorithm
def initialize(context):
    # Path to the adjusted CSV data directory
    csv_data_directory = './Data/daily'  # Update this path
    
    # List all CSV files in the directory
    csv_files = [f for f in os.listdir(csv_data_directory) if f.endswith('.csv')]
    
    # Extract stock symbols from filenames (remove '.csv' extension)
    stock_symbols = [os.path.splitext(f)[0] for f in csv_files]
    # print(stock_symbols)
    
    # Create Zipline symbols for all stocks
    context.stock_universe = symbols(*stock_symbols)
    
    # Define parameters
    context.lookback = 7  # Lookback period in days
    context.holding_period = 7 # Holding period in days
    
    # Initialize variables
    context.stock_list = []  # List to hold selected stocks
    context.stock_num = []
    context.day_count = 0  # Counter to manage the holding period
    context.previous_day = None
    context.previous_nav_update = None
    context.first_time = True
    context.just_bought = False
    context.prev_prices = None
    context.prev_week = None
    context.prev_month = None
    context.prev_year = None
    context.prev_three_mon = None
    context.prev_six_mon = None

    # Convert to a set
    context.date_set = set()
    # print (context.date_set)

    # Initialize dataframe to store NAV, stock names, and prices
    dates = pd.date_range(start='2012-10-01', end='2023-08-10', freq='B')  # Business days between start and end date
    columns = ['NAV'] + [f'Ticker_{i}' for i in range(1, 51)] + [f'Name_{i}' for i in range(1, 51)] + [f'Price_{i}' for i in range(1, 51)] + [f'PriceRatio{i}' for i in range(1, 51)]
    context.nav_data = pd.DataFrame(index=dates, columns=columns)
    context.nav_data = context.nav_data.fillna(0)  # Initializing with zeros
    context.prev_top_stock_prices = [(None, 0) for _ in range(50)]

from pandas import DateOffset

def get_date_from_NAV(context, data):
    
    if context.lookback == 7:
        current_day = data.current_session
        prev_day = current_day - pd.DateOffset(weeks=1)
        if current_day == pd.Timestamp('2013-09-16'):
            print("DEBUGG")
        store = prev_day
        # print(f'Current Day: {current_day}, Previous Week Day: {prev_day}')
        while prev_day not in context.date_set:
            prev_day += pd.DateOffset(days=1)
        return prev_day
    elif context.lookback == 21:
        current_day = data.current_session
        prev_day = current_day - pd.DateOffset(months=1)
        while prev_day not in context.date_set:
            prev_day += pd.DateOffset(days=1)
        return prev_day
    elif context.lookback == 63:
        current_day = data.current_session
        prev_day = current_day - pd.DateOffset(months=3)
        while prev_day not in context.date_set:
            prev_day += pd.DateOffset(days=1)
        return prev_day
    elif context.lookback == 126:
        current_day = data.current_session
        prev_day = current_day - pd.DateOffset(months=6)
        while prev_day not in context.date_set:
            prev_day += pd.DateOffset(days=1)
        return prev_day
    elif context.lookback == 252:
        current_day = data.current_session
        prev_day = current_day - pd.DateOffset(years=1)
        while prev_day not in context.date_set:
            prev_day += pd.DateOffset(days=1)
        return prev_day


from datetime import timedelta

def largest_50(returns):
    top_stocks = []
    returns = returns.sort_values(ascending=False)
    # Drop NAN values
    returns = returns.dropna()
    return returns[:50].index

def handle_data(context, data):
    
    context.day_count += 1
    current_day = data.current_session
    print(current_day)
    context.date_set.add(current_day)

    if (current_day == pd.Timestamp('2013-07-04')):
        print("ADdasdas")
    
    if context.day_count < context.lookback:


        if context.prev_week is None or (current_day - context.prev_week).days >= 7 or current_day.weekday() == 0:
            context.prev_week = current_day

        if context.previous_day is None or (current_day.month != context.previous_day.month or current_day.year != context.previous_day.year):
            context.prev_month = current_day
        
        if context.previous_day is None or (current_day.year != context.previous_day.year):
            context.prev_year = current_day

        if context.prev_three_mon is None or (current_day.year == context.prev_three_mon.year and current_day.month - context.prev_three_mon.month == 3) or (current_day.year - context.prev_three_mon.year == 1 and current_day.month + 12 - context.prev_three_mon.month == 3):
            # print("Current:", current_day)
            # print("Previous:", context.prev_three_mon)
            context.prev_three_mon = current_day
        

        if context.previous_day is None or (current_day.year == context.prev_six_mon.year and current_day.month - context.prev_six_mon.month == 6) or (current_day.year - context.prev_six_mon.year == 1 and current_day.month + 12 - context.prev_six_mon.month == 6):
            context.prev_six_mon = current_day
        return
    
    
    # Check for Weekly rebalancing
    if context.previous_nav_update is None or (current_day - context.previous_nav_update).days >= 7 or current_day.weekday() == 0:
        # Sell all existing positions
        for stock in context.portfolio.positions:
            order_target_percent(stock, 0)
        
        context.stock_list = []
        context.stock_num = []

        # Buy new stocks based on momentum
        which_prev = get_date_from_NAV(context, data)
        # print(f'Current Day: {current_day}, Previous Day: {which_prev}')
        prices = data.history(context.stock_universe, 'price', (current_day - which_prev).days-1, '1d')
        # print(prices.iloc[0])
        # print(prices.iloc[-1])
        # context.nav_data.at[current_day, 'LookBackDate'] = context.previous_nav_update
        returns = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
        top_stocks = largest_50(returns)
        if len(top_stocks) < 50:
            print(f'Current Day: {current_day}, Previous Day: {context.previous_nav_update}, {len(top_stocks)} stocks found')
            print(prices)
            print(which_prev)
            
        # print(returns)
        context.stock_list = top_stocks
        # print(top_stocks)
        if len(context.stock_list) > 0:
            for i, stock in enumerate(context.stock_list):
                stock_price = data.current(stock, 'price')
                allocated_capital = context.portfolio.portfolio_value / len(context.stock_list)
                num_shares = allocated_capital / stock_price
                context.stock_num.append(num_shares)  # Store the calculated number of shares
                # if current_day == pd.Timestamp('2013-07-11'):
                #     print(f'Stock: {stock.symbol}')
                # Place the order
                order_value(stock, allocated_capital)

        context.just_bought = True
        if context.previous_nav_update is not None:
            for i, (stock_symbol, prev_price) in enumerate(context.prev_top_stock_prices):
                cur_price = data.current(stock_symbol, 'price')
                price_ratio = cur_price / prev_price if prev_price != 0 else 1
                # print(cur_price)
                # print(prev_price)
                # print(context.previous_nav_update, stock_symbol, price_ratio)
                # if context.previous_nav_update == pd.Timestamp('2013-07-11'):
                #     print(f'Stock: {stock_symbol}')
                context.nav_data.at[context.previous_nav_update, f'PriceRatio{i+1}'] = price_ratio

            # print(context.nav_data.loc[context.previous_nav_update])

        for i, stock in enumerate(context.stock_list):
            stock_price = data.current(stock, 'price')
            context.prev_top_stock_prices[i] = (stock, stock_price)
        
        # print(len(context.portfolio.positions))
        # Update value of each stock in the portfolio
        tot_value = 0

        
        for i in range(50):
            stock = context.stock_list[i]
            num_shares = context.stock_num[i] if i < len(context.stock_num) else 0

            # Calculate the value of each stock holding
            stock_price = data.current(stock, 'price')
            stock_value = num_shares * stock_price
            tot_value += stock_value

            # Update the NAV data with stock information
            context.nav_data.at[current_day, f'Price_{i+1}'] = stock_value
            context.nav_data.at[current_day, f'Ticker_{i+1}'] = stock.symbol
            context.nav_data.at[current_day, f'Name_{i+1}'] = ticketToName.get(stock.symbol + ' IN', 'Unknown')
        context.nav_data.at[current_day, 'NAV'] = tot_value
        

        context.previous_nav_update = current_day
        
        context.prev_prices = [data.current(stock, 'price') for stock in context.stock_list]
        
    if context.prev_week is None or (current_day - context.prev_week).days >= 7 or current_day.weekday() == 0:
        context.prev_week = current_day
    context.just_bought = False  
     
    if context.previous_day is None or (current_day.month != context.previous_day.month or current_day.year != context.previous_day.year):
        context.prev_month = current_day 
        # print(context.prev_month, context.prev_month.weekday())
    
    if context.previous_day is None or (current_day.year != context.previous_day.year):
        context.prev_year = current_day
        # print(context.prev_year, context.prev_year.weekday(), context.previous_day)
    
    if context.prev_three_mon is None or (current_day.year == context.prev_three_mon.year and current_day.month - context.prev_three_mon.month == 3) or (current_day.year - context.prev_three_mon.year == 1 and current_day.month + 12 - context.prev_three_mon.month == 3):
        # print("Current:", current_day)
        # print("Previous:", context.prev_three_mon)
        context.prev_three_mon = current_day
        

    if context.prev_six_mon is None or (current_day.year == context.prev_six_mon.year and current_day.month - context.prev_six_mon.month == 6) or (current_day.year - context.prev_six_mon.year == 1 and current_day.month + 12 - context.prev_six_mon.month == 6):
        print("Current:", current_day)
        print("Previous:", context.prev_six_mon)
        context.prev_six_mon = current_day
    context.previous_day = current_day

        




def analyze(context, perf):
    # print(context.nav_data)
    # Save the nav_data DataFrame to Excel
    context.nav_data = context.nav_data[context.nav_data.NAV != 0]  # Remove rows with no trades
    # os.mkdir('NewResults', exist_ok=True)
    os.chdir('NewResults')
    name = 'Lookback_' + str(context.lookback) + '_Holding_' + str(context.holding_period)
    context.nav_data.to_excel(name+'.xlsx')


if __name__ == '__main__':
    start_date = pd.Timestamp('2013-7-2') # 02-07-2012
    end_date = pd.Timestamp('2023-08-10')

    calendar = get_calendar('XBOM')

    # Get the first 10 trading days starting from your start date
    trading_days = calendar.sessions_in_range(start_date, end_date)
    first_10_trading_days = trading_days[trading_days.get_loc(start_date):][:10]
    print(first_10_trading_days)
    result = run_algorithm(
        start=start_date,
        end=end_date,
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        bundle='my_custom_bundle',
        capital_base=10_00_000,
    )
