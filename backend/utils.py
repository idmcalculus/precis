import logging
import os
import pandas as pd
from database import db
from models import RainfallData
from logging.handlers import RotatingFileHandler
from flask.logging import default_handler

def populate_db_from_excel():
    DATA_PATH = "./data/Data.xlsx"
    df = pd.read_excel(DATA_PATH)
    for index, row in df.iterrows():
        record = RainfallData(time=row['time'], RG_A=row['RG_A'])
        db.session.add(record)
        db.session.commit()

def configure_logging(app):
    # Logging Configuration
    if app.config['LOG_WITH_GUNICORN']:
        gunicorn_error_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers.extend(gunicorn_error_logger.handlers)
        app.logger.setLevel(logging.DEBUG)
    else:
        file_handler = RotatingFileHandler('instance/precis-api.log',
                                           maxBytes=16384,
                                           backupCount=20)
        file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(threadName)s-%(thread)d: %(message)s [in %(filename)s:%(lineno)d]')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    # Remove the default logger configured by Flask
    app.logger.removeHandler(default_handler)

    app.logger.info('Starting the Precis API App...')
