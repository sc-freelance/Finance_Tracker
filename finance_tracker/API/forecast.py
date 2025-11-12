from flask_restful import Resource
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from flask import request, jsonify
from io import StringIO
import pandas as pd 
import numpy as np
import os

UPLOADS = 'uploads/'

class ForecastAPI(Resource):
    def get(self):
        # Model type and polynomial degree from frontend
        model_type = request.args.get('model', 'polynomial').lower()
        degree = int(request.args.get('degree', 3))

        # Get latest uploaded CSV file
        files = [f for f in os.listdir(UPLOADS) if f.endswith('.csv')]
        if not files:
            return {'error': 'No uploaded data available'}, 400
        
        filepath = os.path.join(UPLOADS, files[-1])
        df = pd.read_csv(filepath)

        # Validate file structure
        if not {'Date', 'Amount'}.issubset(df.columns):
            return {'error': 'CSV must contain Date and Amount columns'}, 400

        # Prepare data        
        df['Date'] = pd.to_datetime(df['Date'])
        df['Days'] = (df['Date'] - df['Date'].min()).dt.days
        x = df['Days'].values.reshape(-1, 1)
        y = df['Amount'].values

        # Model selection and fitting
        if model_type == 'linear':
            model = LinearRegression()
            model_name = "Linear Regression"
        else:
            model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
            model_name = f"polynomial Regression (Degree {degree})"
        
        # Train the model
        model.fit(x, y)

        # Prediction for the next month
        future = pd.DataFrame({
            'Days': range(df['Days'].max() + 1, df['Days'].max() + 31)
        })
        prediction = model.predict(future)
        prediction = [round(float(p), 2) for p in prediction]

        return {
            'forecast': prediction,
            'model_used': model_name,
            'points_trained': len(df)
        }