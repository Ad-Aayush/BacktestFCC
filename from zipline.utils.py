import exchange_calendars as ecals
import pandas as pd

# Get the XBOM trading calendar
xbom_cal = ecals.get_calendar("XBOM")

# Define the date range
start_date = pd.Timestamp("2012-07-02")
end_date = pd.Timestamp("2023-08-10")

# Get the valid trading sessions as strings
trading_sessions_str = xbom_cal.sessions_in_range(start_date, end_date).astype(str)

# Convert back to Timestamp objects with timezone information
trading_sessions = pd.to_datetime(trading_sessions_str, utc=True)

# Print or use the trading sessions as needed
print(trading_sessions)
