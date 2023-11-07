import pandas as pd
import os
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
from zipline import run_algorithm
from zipline.api import symbols, order_target_percent
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
    context.holding_period = 21 # Holding period in days
    
    # Initialize variables
    context.stock_list = []  # List to hold selected stocks
    context.day_count = 0  # Counter to manage the holding period
    
    # Initialize dataframe to store NAV, stock names, and prices
    dates = pd.date_range(start='2012-10-01', end='2023-08-10', freq='B')  # Business days between start and end date
    columns = ['NAV'] + [f'Ticker_{i}' for i in range(1, 51)] + [f'Name_{i}' for i in range(1, 51)] + [f'Price_{i}' for i in range(1, 51)]
    context.nav_data = pd.DataFrame(index=dates, columns=columns)
    context.nav_data = context.nav_data.fillna(0)  # Initializing with zeros



def handle_data(context, data):
    context.day_count += 1
    
    # If the holding period is over, liquidate all positions
    if context.day_count > context.holding_period:
        for stock in context.portfolio.positions:
            order_target_percent(stock, 0)
        context.stock_list = []
        context.day_count = 0
        
    # If it's time to rebalance, select the top 50 stocks
    if context.day_count == 0:
        prices = data.history(context.stock_universe, 'price', context.lookback, '1d')
        returns = (prices.iloc[-1] - prices.iloc[0]) / prices.iloc[0]
        top_stocks = returns.nlargest(50).index
        context.stock_list = top_stocks
        
        if len(context.stock_list) > 0:
            # Allocate equal weight to each stock
            for stock in context.stock_list:
                order_target_percent(stock, 1.0 / len(context.stock_list))
            
            # Store selected stocks and their current prices in nav_data DataFrame
            date = data.current_session
            context.nav_data.at[date, 'NAV'] = context.portfolio.portfolio_value
            for i, stock in enumerate(context.stock_list, start=1):
                context.nav_data.at[date, f'Ticker_{i}'] = stock.symbol
                context.nav_data.at[date, f'Name_{i}'] = ticketToName[stock.symbol+' IN']
                context.nav_data.at[date, f'Price_{i}'] = data.current(stock, 'price')
        else:
            print("No stocks selected for rebalance on", data.current_session)

        




def analyze(context, perf):
    # print(context.nav_data)
    # Save the nav_data DataFrame to Excel
    context.nav_data = context.nav_data[context.nav_data.NAV != 0]  # Remove rows with no trades
    os.mkdir('Results', exist_ok=True)
    os.chdir('Results')
    name = 'Lookback_' + str(context.lookback) + '_Holding_' + str(context.holding_period)
    context.nav_data.to_excel(name+'.xlsx')


# Run the backtest
if __name__ == '__main__':
    start_date = pd.Timestamp('2013-7-12')
    end_date = pd.Timestamp('2023-08-10')


    result = run_algorithm(
        start=start_date,
        end=end_date,
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        bundle='my_custom_bundle',
        capital_base=10000,
    )
