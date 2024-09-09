import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
import json
import random
import sqlite3

from sqlalchemy import create_engine, inspect
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from plotly.utils import PlotlyJSONEncoder

from database import db
from models import RainfallData
from utils import filter_data, handle_nan, populate_db_from_excel
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='./static')

    if os.environ.get('FLASK_ENV') == 'development':
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    db.init_app(app)

    CORS(app)

    with app.app_context():
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        inspector = inspect(engine)

        if not inspector.has_table("rainfall_data"):
            print('Table does not exist, creating all database tables...')
            db.create_all()
            print('Database tables created!')

            print('Populating database from Excel...')
            populate_db_from_excel()
            print('Database populated from Excel!')
        else:
            print('Database already exists!')
            if RainfallData.query.count() == 0:
                populate_db_from_excel()

        # Add this line to check the number of records after initialization
        print('Number of records in database:', RainfallData.query.count())


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

        print("DataFrame columns:", df.columns)
        print("DataFrame head:", df.head())

        df = filter_data(df)

        # Create scatter plot for rainfall data
        scatter_fig = px.scatter(df, x='time', y='RG_A', title='Rainfall Over Time')
        scatter_fig.update_traces(marker=dict(size=5, color=[f'rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})' for _ in range(len(df))]))
        
        # Create bar chart for value counts with logarithmic y-axis
        value_counts = df['RG_A'].value_counts().reset_index()
        value_counts.columns = ['RG_A', 'count']
        bar_fig = px.bar(value_counts, x='RG_A', y='count', title='Frequency of Rainfall Data')
        bar_fig.update_traces(marker_color=[f'rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)})' for _ in range(len(value_counts))])
        bar_fig.update_layout(yaxis_type="log")
    
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
        
        # value_counts = df['RG_A'].value_counts().to_dict() # Get unique value counts

        result = {
            "scatter_chart": json.dumps(scatter_fig, cls=PlotlyJSONEncoder),
            "bar_chart": json.dumps(bar_fig, cls=PlotlyJSONEncoder),
            "statistics": statistics
        }

        return jsonify(result)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
