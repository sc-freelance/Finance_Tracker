from flask import Flask, render_template, request, jsonify
from flask_restful import Api
from API.expenses import ExpenseAPI
from API.forecast import ForecastAPI
import os
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)
api = Api(app)

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'csv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Register RESTful endpoints
api.add_resource(ExpenseAPI, '/api/expenses')
api.add_resource(ForecastAPI, '/api/forecast')

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        df = pd.read_csv(filepath)

        # Validate file structure
        if not {'Date', 'Amount'}.issubset(df.columns):
            return jsonify({'error': 'CSV must contain Date and Amount columns'}), 400

        return jsonify({'message': f'{filename} uploaded successfully'}), 200

    return jsonify({'error': 'Invalid file type'}), 400


if __name__ == "__main__":
    app.run(debug=True)