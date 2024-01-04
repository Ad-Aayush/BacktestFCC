import pandas as pd
import os
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
from zipline import run_algorithm
from zipline.api import symbols, order_target_percent, order_value, get_open_orders
import warnings
warnings.filterwarnings("ignore")

import json 

f = open('./BacktestingData/mydata.json')
ticketToName = json.load(f)
print(ticketToName) 

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
    context.lookback = 252  # Lookback period in days
    context.holding_period = 7 # Holding period in days
    
    # Initialize variables
    context.stock_list = []  # List to hold selected stocks
    context.stock_num = []
    context.day_count = 0  # Counter to manage the holding period
    context.previous_day = None
    context.previous_nav_update = None
    context.first_time = True
    context.just_bought = False
    # Initialize dataframe to store NAV, stock names, and prices
    dates = pd.date_range(start='2012-10-01', end='2023-08-10', freq='B')  # Business days between start and end date
    columns = ['NAV'] + [f'Ticker_{i}' for i in range(1, 51)] + [f'Name_{i}' for i in range(1, 51)] + [f'Price_{i}' for i in range(1, 51)]
    context.nav_data = pd.DataFrame(index=dates, columns=columns)
    context.nav_data = context.nav_data.fillna(0)  # Initializing with zeros



from datetime import timedelta

def handle_data(context, data):
    context.day_count += 1

    if context.day_count < context.lookback:
        return
    current_day = data.current_session
    
    # Check for Weekly rebalancing
    if context.previous_day is None or (current_day - context.previous_day).days >= 7:
        # Sell all existing positions
        for stock in context.portfolio.positions:
            order_target_percent(stock, 0)
        
        context.stock_list = []
        context.stock_num = []

        # Buy new stocks based on momentum
        prices = data.history(context.stock_universe, 'price', context.lookback, '1d')
        returns = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
        top_stocks = returns.nlargest(50).index
        context.stock_list = top_stocks
        
        if len(context.stock_list) > 0:
            for stock in context.stock_list:
                stock_price = data.current(stock, 'price')
                allocated_capital = context.portfolio.portfolio_value / len(context.stock_list)
                num_shares = allocated_capital / stock_price
                context.stock_num.append(num_shares)  # Store the calculated number of shares

                # Place the order
                order_value(stock, allocated_capital)

        context.just_bought = True
        context.previous_day = current_day  # Update the last trading day

    # Weekly update of NAV and stock values
    if context.previous_nav_update is None or (current_day - context.previous_nav_update).days >= 7:
        # Update NAV
        
        # print(len(context.portfolio.positions))
        # Update value of each stock in the portfolio
        tot_value = 0

        if context.just_bought:
            for i, stock in enumerate(context.stock_list, start=1):
                # Assuming equal investment in each stock
                stock_value = context.portfolio.portfolio_value / len(context.stock_list) 
                tot_value += stock_value
                context.nav_data.at[current_day, f'Price_{i}'] = stock_value
                context.nav_data.at[current_day, f'Ticker_{i}'] = stock.symbol
                context.nav_data.at[current_day, f'Name_{i}'] = ticketToName.get(stock.symbol + ' IN', 'Unknown')
        else:
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

    context.just_bought = False    
    context.previous_day = data.current_session

        




def analyze(context, perf):
    # print(context.nav_data)
    # Save the nav_data DataFrame to Excel
    context.nav_data = context.nav_data[context.nav_data.NAV != 0]  # Remove rows with no trades
    # os.mkdir('NewResults', exist_ok=True)
    os.chdir('NewResults')
    name = 'Lookback_' + str(context.lookback) + '_Holding_' + str(context.holding_period)
    context.nav_data.to_excel(name+'.xlsx')


# Run the backtest
if __name__ == '__main__':
    start_date = pd.Timestamp('2013-7-2') # 02-07-2012
    end_date = pd.Timestamp('2023-08-10')


    result = run_algorithm(
        start=start_date,
        end=end_date,
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        bundle='my_custom_bundle',
        capital_base=10_00_000,
    )
