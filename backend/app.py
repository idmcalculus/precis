import pandas as pd
import os
from sqlalchemy import create_engine, inspect
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from database import db
from models import RainfallData
from utils import filter_data, handle_nan, populate_db_from_excel
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv
import sqlite3

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
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
