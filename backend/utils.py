import pandas as pd
from database import db
from models import RainfallData

def populate_db_from_excel():
    DATA_PATH = "./data/Data.xlsx"
    df = pd.read_excel(DATA_PATH)
    for index, row in df.iterrows():
        record = RainfallData(time=row['time'], RG_A=row['RG_A'])
        db.session.add(record)
        db.session.commit()
