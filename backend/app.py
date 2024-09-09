import pandas as pd
import os
import plotly.express as px
import plotly.graph_objects as go
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from plotly.utils import PlotlyJSONEncoder
import json
import random
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
