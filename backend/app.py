import pandas as pd
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from utils import filter_data, handle_nan, load_data_from_excel
from config import DevelopmentConfig, ProductionConfig
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, static_folder='./static')

    if os.environ.get('FLASK_ENV') == 'development':
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    CORS(app)

    @app.route('/', defaults={'path': 'index.html'})
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)

    @app.route('/api/data', methods=['GET'])
    def get_data():
        df = load_data_from_excel()
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
            "data": df.to_dict(orient='records'),
            "statistics": statistics,
            "value_counts": value_counts
        }

        return jsonify(result)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
