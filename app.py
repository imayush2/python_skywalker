from flask import Flask, jsonify, request
import subprocess
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS 

@app.route('/scrape', methods=['POST'])
def run_test_script():
    try:
        # Get the selected diseases from the POST request
        data = request.get_json()
        selected_diseases = data.get('selectedDiseases', [])
        
        # Ensure at least one disease is selected
        if not selected_diseases:
            return jsonify({'message': 'No diseases selected'}), 400

        # Call test.py for each selected disease
        for disease in selected_diseases:
            # Pass the disease as a command-line argument to test.py
            result = subprocess.run(['python3', 'test.py', disease], capture_output=True, text=True)

            # Log the result to understand what is happening
            print(f"Running test.py for disease: {disease}")
            print(f"Result stdout: {result.stdout}")
            print(f"Result stderr: {result.stderr}")

            # Check the result of the script execution
            if result.returncode != 0:
                return jsonify({'message': 'Script execution failed', 'error': result.stderr}), 500

        return jsonify({'message': 'Script executed successfully', 'output': 'Scraping completed for selected diseases'}), 200

    except Exception as e:
        return jsonify({'message': 'Error occurred', 'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)  # Running on http://127.0.0.1:5000
