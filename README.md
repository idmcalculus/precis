# Precis: A Rainfall Visualization Web Application

## Overview

"Precis" is a web-based application designed to visualize timeseries rainfall data. With an elegant user interface, the app aims to provide insightful visual representations of rainfall patterns over time. Located at the heart of central Birmingham, our data source captures rainfall with high precision, presenting users with a detailed view of climate patterns.

## Features

- **Timeseries Visualization**: At the core of "Precis" is a dynamic timeseries graph that plots rainfall data, providing users with an intuitive understanding of rainfall trends.
  
- **Interactive Map**: Integrated within the app is an interactive map pinpointing the location of our rain gauge in central Birmingham. Users can get spatial context alongside the timeseries data.
  
- **Date Range Picker**: To cater to the diverse needs of our users, "Precis" offers a date range picker, allowing users to zoom into specific intervals of interest.

## Future Enhancements

- **Zoom & Pan on Graph**: To give users more control over data inspection.
  
- **Data Export Options**: Allowing users to download the visualized data for offline analysis.

- **User Accounts & Personalization**: Users could save their preferred settings and access historical data views.

## Getting Started

### Backend Setup

1. **Activate the virtual environment** (assuming you're using one):

   ```bash
   source venv/bin/activate  # for Unix-based systems
   venv\Scripts\activate     # for Windows
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server to Initialize and populate the database**:

   Run the `app.py` file directly. This will create the necessary SQLite tables and populate them with data from the provided Excel file.

   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to the frontend directory**:

   ```bash
   cd ./frontend
   ```

2. **Install frontend dependencies**:

   ```bash
   npm install
   ```

3. **Start the frontend server**:

   ```bash
   npm start
   ```

Now, both the backend and frontend servers should be running. Visit the frontend URL, usually `http://localhost:3000`, in your web browser to view the application.


Stay tuned for more updates as "Precis" continues to evolve!