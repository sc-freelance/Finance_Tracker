from flask_restful import Resource
from flask import request, jsonify
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import os
import traceback

UPLOADS = "uploads"

class ForecastAPI(Resource):
    def get(self):
        try:
            # --- query params ---
            model_type = (request.args.get('model', 'polynomial') or 'polynomial').lower()
            degree_raw = request.args.get('degree', '2')
            try:
                degree = max(2, min(6, int(degree_raw)))  # clamp 2..6
            except ValueError:
                degree = 2

            # --- find latest CSV ---
            if not os.path.isdir(UPLOADS):
                return jsonify(error="Uploads folder not found"), 400

            files = [f for f in os.listdir(UPLOADS) if f.lower().endswith('.csv')]
            if not files:
                return jsonify(error="No uploaded data available"), 400

            files.sort(key=lambda f: os.path.getmtime(os.path.join(UPLOADS, f)))
            filepath = os.path.join(UPLOADS, files[-1])

            # --- load & validate ---
            df = pd.read_csv(filepath)

            required = {'Date', 'Amount'}
            if not required.issubset(df.columns):
                return jsonify(error="CSV must contain Date and Amount columns"), 400

            # clean up types
            df = df.copy()
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

            df = df.dropna(subset=['Date', 'Amount'])
            if df.empty:
                return jsonify(error="No valid rows after parsing Date/Amount."), 400

            # sort and engineer feature
            df = df.sort_values('Date')
            df['Days'] = (df['Date'] - df['Date'].min()).dt.days

            if df['Days'].nunique() < 2:
                return jsonify(error="Not enough distinct dates to train a model."), 400

            X = df[['Days']]
            y = df['Amount']

            # --- choose model ---
            if model_type == 'linear' or len(df) < 4:
                model = LinearRegression()
                model_name = "Linear Regression"
            else:
                model = make_pipeline(PolynomialFeatures(degree=degree), LinearRegression())
                model_name = f"Polynomial Regression (Degree {degree})"

            # --- fit & predict ---
            model.fit(X, y)

            horizon = 30
            future_days = pd.Series(range(int(df['Days'].max()) + 1, int(df['Days'].max()) + 1 + horizon))
            future = pd.DataFrame({'Days': future_days})
            preds = model.predict(future)
            preds = [round(float(p), 2) for p in preds]

            # labels for past & future
            past_labels = df['Date'].dt.strftime('%Y-%m-%d').tolist()
            past_values = df['Amount'].round(2).tolist()

            future_dates = pd.date_range(df['Date'].max() + pd.Timedelta(days=1), periods=horizon)
            future_labels = [d.strftime('%Y-%m-%d') for d in future_dates]

            return jsonify({
                'model_used': model_name,
                'points_trained': int(len(df)),
                'past': {'labels': past_labels, 'values': past_values},
                'forecast': {'labels': future_labels, 'values': preds}
            })

        except Exception as e:
            # print full stack to server console and return JSON error
            traceback.print_exc()
            return jsonify(error=f"Server error: {str(e)}"), 500