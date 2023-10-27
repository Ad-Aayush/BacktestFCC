import pandas as pd
import os
from zipline.data.bundles import register
from zipline.data.bundles.csvdir import csvdir_equities
from zipline import run_algorithm
from zipline.api import symbols, order_target_percent
import warnings
warnings.filterwarnings("ignore")

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
    print(stock_symbols)
    # Create Zipline symbols for all stocks
    context.stock_universe = symbols(*stock_symbols)
    
    # Define parameters
    context.lookback = 20  # Lookback period in days
    context.holding_period = 5  # Holding period in days
    
    # Initialize variables
    context.stock_list = []  # List to hold selected stocks
    context.day_count = 0  # Counter to manage the holding period
    context.portfolio_weights = {}  # Dictionary to store portfolio weights


def handle_data(context, data):
    for stock in context.stock_universe:
        volume = data.current(stock, 'volume')
        print("Volume of {} on {}: {}".format(stock.symbol, data.current_session, volume))
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
        
        # Debug: Print prices and returns
        # print("Prices:\n", prices.head())
        # print("Returns:\n", returns.head())
        
        top_stocks = returns.nlargest(50).index
        context.stock_list = top_stocks
        
        if len(context.stock_list) > 0:
            # Allocate equal weight to each stock
            for stock in context.stock_list:
                order_target_percent(stock, 1.0 / len(context.stock_list))
            
            # Store portfolio weights
            date = data.current_session
            context.portfolio_weights[date] = {stock.symbol: 1.0 / len(context.stock_list) for stock in context.stock_list}
        else:
            print("No stocks selected for rebalance on", data.current_session)
        # open_orders = open_orders()
        # if open_orders:
        #     print("Open Orders on {}: {}".format(data.current_session, open_orders))
        




def analyze(context, perf):
    # Creating DataFrame for portfolio weights
    weights_df = pd.DataFrame.from_dict(context.portfolio_weights, orient='index')
    
    # Creating DataFrame for NAV output
    nav_df = pd.DataFrame({'Date': perf.index.tz_localize(None), 'NAV': perf.portfolio_value})
    
    # Merging NAV and portfolio weights
    output_df = pd.merge(nav_df, weights_df, left_on='Date', right_index=True, how='left')
    
    # Filling NaN values with 0 (for days when no rebalance happened)
    output_df.fillna(0, inplace=True)
    
    # Saving to Excel
    output_df.to_excel('nav_output.xlsx', index=False)


# Run the backtest
if __name__ == '__main__':
    start_date = pd.Timestamp('2013-10-01')
    end_date = pd.Timestamp('2014-2-1')


    result = run_algorithm(
        start=start_date,
        end=end_date,
        initialize=initialize,
        handle_data=handle_data,
        analyze=analyze,
        bundle='my_custom_bundle',
        capital_base=10000,
    )
