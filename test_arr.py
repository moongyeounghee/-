import sys
import arrival_flight_api

print("Testing Arrival API...")
try:
    df = arrival_flight_api.get_arrivals_data()
    if df.empty:
        print("API returned an empty DataFrame.")
    else:
        print(f"Success! Fetched {len(df)} rows.")
        print(df.head(2))
except Exception as e:
    import traceback
    print(f"Exception occurred:\n{traceback.format_exc()}")
