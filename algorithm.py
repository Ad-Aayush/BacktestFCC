import pandas as pd
import os
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
from zipline import run_algorithm
from zipline.api import symbols, order_target_percent

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
    csv_data_directory = './Data'  # Update this path
    
    # List all CSV files in the directory
    csv_files = [f for f in os.listdir(csv_data_directory) if f.endswith('.csv')]
    
    # Extract stock symbols from filenames (remove '.csv' extension)
    stock_symbols = [os.path.splitext(f)[0] for f in csv_files]
    
    # Create Zipline symbols for all stocks
    context.stock_universe = symbols(*stock_symbols)
    
    # Define parameters
    context.lookback = 20  # Lookback period in days
    context.holding_period = 5  # Holding period in days
    
    # Initialize variables
    context.stock_list = []  # List to hold selected stocks
    context.day_count = 0  # Counter to manage the holding period

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
        
        # Allocate equal weight to each stock
        for stock in context.stock_list:
            order_target_percent(stock, 1.0 / len(context.stock_list))

def analyze(context, perf):
    # Analysis code
    pass

# Run the backtest
if __name__ == '__main__':
    start_date = pd.Timestamp('2013-10-01', tz='utc')
    end_date = pd.Timestamp('2023-8-10', tz='utc')

    result = run_algorithm(
        start=start_date,
        end=end_date,
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        bundle='my_custom_bundle',
        capital_base=10000,
    )
