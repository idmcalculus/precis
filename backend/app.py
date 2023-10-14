from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

# Load the data when the application starts
data_path = "./data/Data.xlsx"
df = pd.read_excel(data_path)

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(df.to_dict(orient='records')) # Convert the dataframe to a dictionary and return it as JSON

if __name__ == '__main__':
    app.run(debug=True)
