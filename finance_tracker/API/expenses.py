from flask_restful import Resource
from flask import request, jsonify
import pandas as pd

# ExpenseAPI handles CRUD operations for expenses
class ExpenseAPI(Resource):
    def get(self):
        try: 
            # Load expenses from a CSV file (for demonstration purposes)
            df = pd.read_csv('uploads/expenses.csv')

            # Convert 'Date' column to datetime and return as JSON
            expenses = df.to_datetime('Date').dt.strftime('%Y-%m-%d').to_dict()
            return jsonify(expenses)
        
        # Handle file not found or other exceptions
        except FileNotFoundError:
            return jsonify({'error': 'Expenses file not found'}), 404