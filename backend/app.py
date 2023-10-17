import pandas as pd
import os
import sqlalchemy as sa
from flask import Flask, jsonify, request, abort, send_from_directory
from flask_cors import CORS
from database import db
from utils import populate_db_from_excel
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv
import sqlite3

load_dotenv()

app = Flask(__name__, static_folder='./static')

if os.environ.get('FLASK_ENV') == 'development':
    app.config.from_object(DevelopmentConfig)
else:
    app.config.from_object(ProductionConfig)

db.init_app(app)

from models import RainfallData

CORS(app)

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

@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/api/exportdb', methods=['GET'])
def exportdb():
    con = sqlite3.connect("instance/rainfall_data.db")
    with open("exports.sql", 'w') as f:
        for line in con.iterdump():
            f.write('%s\n' % line)
    con.close()
    return "Database exported!"

@app.route('/api/data', methods=['GET'])
def get_data():
    data_query = RainfallData.query.all()
    data_records = [entry.as_dict() for entry in data_query]  # Convert ORM objects to dictionaries
    df = pd.DataFrame(data_records)  # Convert dictionaries to DataFrame

    df = filter_data(df)
    
    # Calculate statistical values
    statistics = {
        "mean": handle_nan(df['RG_A'].mean()),
        "median": handle_nan(df['RG_A'].median()),
        "standard_deviation": handle_nan(df['RG_A'].std()),
        "range": handle_nan(df['RG_A'].max() - df['RG_A'].min()),
        "highest": handle_nan(df['RG_A'].max()),
        "lowest": handle_nan(df['RG_A'].min()),
        "total_count": df['RG_A'].count().item()
    }
    
    value_counts = df['RG_A'].value_counts().to_dict() # Get unique value counts

    result = {
        "data": data_records,
        "statistics": statistics,
        "value_counts": value_counts
    }

    return jsonify(result)

if __name__ == '__main__':
    print('Initializing the database...')

    engine = sa.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    inspector = sa.inspect(engine)

    print(app.config['SQLALCHEMY_DATABASE_URI'])
    print('Checking if the database already contains the rainfall_data table...')
    print(inspector.has_table("rainfall_data"))

    # Check if the table exists
    if not inspector.has_table("rainfall_data"):
        with app.app_context():
            db.create_all()
            print('Initialized the database!')

    # Check if data exists in the table
    with app.app_context():
        if not RainfallData.query.first():  # No data in the table
            populate_db_from_excel()  # Populate database with data from Excel file
            print('Populated the database from Excel!')

    print('Database already contains the rainfall_data table.')
    app.run()
