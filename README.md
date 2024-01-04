# Backtesting

*Finance & Consulting Club*

---

## Table of Contents

1. [Choice of Library](#choice-of-library)
2. [Data Organization](#data-organization)
3. [Implementing the Strategy](#implementing-the-strategy)
4. [Analysis of the Results](#analysis-of-the-results)

---

## Choice of Library

I identified some basic things that I want from the library I choose to use. First, the library should work well with my custom data. Second, as I have to buy the stocks in equal proportions, I may need to consider fractional buying. The library should be flexible so that I can make changes and optimizations freely. The library should be suitable for making portfolios and not be restricted to a single asset. Looking at all these requirements I chose Zipline Library. It follows all the given requirements, but I may need to write more code.

## Data Organization

Next up, I have to organize the given data per the library's requirements. Each stock's data will occupy its own file with the following columns: Open, Close, High, Low, Volume, Dividends. As I only had a single value, I just took Open = Close = High = Low, assigned an arbitrarily large value to the Volume, and assigned 0 to dividends. Further, the data has to be complete. All the stocks must be present for each day in history. I simply back and forward filled the values. If the stock data for day 3 is available but for day 2 is not, assign day 2 the same data as day 3. This is not ideal, but for most strategies, such values won't cause an issue. This part has been handled in the dataOrganization.ipynb file.

## Implementing the Strategy

First, the organized Excel files must be integrated with Zipline; the code for that is in the ingestData.py file. Now, moving to the algorithm.py file. Each Zipline strategy has 3 main functions: initialize, handle_data, and analyze. We give details of our custom data bundle, the list of stock tickers we are interested in, the look back and holding period and the start and end date of analysis. The main work happens in the handle_data function. We maintain a day_count variable. As soon as the holding period is exceeded, we sell everything we are holding currently and set day_count to 0. We now find the best 50 stocks based on the lookback period and buy them in equal proportion. The details of this are updated in a data frame. Nothing special goes in the analyze function yet. We simply convert the data frame to an Excel file in the results folder, named based on lookback and holding period value.

## Analysis of the Results

Ranking the strategies based on final portfolio value:

| Look Back | Holding Period | Ratio of Final and Initial Portfolio Values | Average Annual Return | Maximum Drawdown |
|-----------|----------------|---------------------------------------------|-----------------------|------------------|
| 12 Month  | 1 Month        | 9.49                                        | 22.70%                | 29.26%           |
| 3 Month   | 1 Month        | 7.93                                        | 20.71%                | 39.89%           |
| 3 Month   | 1 Week         | 4.12                                        | 13.73%                | 33.87%           |
| 1 Month   | 1 Month        | 3.99                                        | 13.41%                | 44.2%            |
| 1 Week    | 1 Week         | 3.56                                        | 12.23%                | 44.23%           |
| 6 Month   | 1 Week         | 3.02                                        | 10.56%                | 26.48%           |
| 6 Month   | 1 Month        | 2.93                                        | 10.25%                | 33.77%           |
| 12 Month  | 1 Week         | 2.43                                        | 8.40%                 | 26.96%           |
| 1 Month   | 1 Week         | 2.19                                        | 7.41%                 | 40.93%           |

Most strategies on the top have a longer (1 Month) Holding Period. Among these, the one with a higher Look Back performs better. The longer the look back period, the lower the maximum drawdown of the strategy.
