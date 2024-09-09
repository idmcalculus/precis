import pandas as pd
from flask import request, abort

def load_data_from_excel():
    DATA_PATH = "./data/Data.xlsx"
    return pd.read_excel(DATA_PATH)

def filter_data(df):
    """Applies various filters to the dataframe based on the request arguments."""
    
    # Date range filter
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    if start_date and end_date:
        df = df[(df['time'] >= start_date) & (df['time'] <= end_date)]
    
    # Specific rainfall filter
    specific_rainfall = request.args.get('specificRainfall')
    if specific_rainfall:
        try:
            df = df[df['RG_A'] == float(specific_rainfall)]
        except ValueError:
            abort(400, "Invalid specificRainfall value")
    
    # Rainfall range filter
    min_rainfall = request.args.get('minRainfall')
    max_rainfall = request.args.get('maxRainfall')
    
    if min_rainfall:
        try:
            df = df[df['RG_A'] >= float(min_rainfall)]
        except ValueError:
            abort(400, "Invalid minRainfall value")

    if max_rainfall:
        try:
            df = df[df['RG_A'] <= float(max_rainfall)]
        except ValueError:
            abort(400, "Invalid maxRainfall value")

    return df

def handle_nan(value, decimal_places=4):
    """Returns None if the value is NaN, otherwise returns the value itself."""
    return round(value, decimal_places) if pd.notna(value) else None