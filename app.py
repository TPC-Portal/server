from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS
import os
import logging
import json
from datetime import datetime

from summarizer import extract_text_from_resume, analyze_resume_with_gemini

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all domains

# Get API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# File to persist last resume
LAST_RESUME_FILE = 'last_resume.json'

def save_last_resume(filename, text, analysis, role='', company=''):
    """Save the last uploaded resume and its analysis to a JSON file."""
    logger.info('Function [save_last_resume] called')
    data = {
        'filename': filename,
        'uploaded_at': datetime.now().isoformat(),
        'role': role,
        'company': company,
        'text': text,
        'analysis': analysis
    }
    try:
        with open(LAST_RESUME_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f'Function [save_last_resume] completed - Saved to {LAST_RESUME_FILE}')
    except Exception as e:
        logger.error(f'Function [save_last_resume] failed - Error: {str(e)}')

def load_last_resume():
    """Load the last uploaded resume data from JSON file."""
    logger.info('Function [load_last_resume] called')
    try:
        if os.path.exists(LAST_RESUME_FILE):
            with open(LAST_RESUME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info('Function [load_last_resume] completed - Data loaded successfully')
            return data
        else:
            logger.info('Function [load_last_resume] completed - No previous resume found')
            return None
    except Exception as e:
        logger.error(f'Function [load_last_resume] failed - Error: {str(e)}')
        return None

@app.route('/', methods=['GET'])
def main():
    logger.info('Function [main] called')
    result = jsonify({'message': 'Hello, World!'})
    logger.info('Function [main] completed')
    return result

@app.route('/last-resume', methods=['GET'])
def get_last_resume():
    logger.info('Function [get_last_resume] called')
    data = load_last_resume()
    if data:
        logger.info('Function [get_last_resume] completed - Returning last resume')
        return jsonify(data)
    else:
        logger.info('Function [get_last_resume] completed - No resume found')
        return jsonify({'error': 'No previous resume found'}), 404

@app.route('/analyze-stages', methods=['POST'])
def analyze_with_stages():
    """Analyze resume with stage-by-stage progress updates."""
    logger.info('Function [analyze_with_stages] called')
    
    # This is a simplified version - for real-time updates, you'd use WebSockets or Server-Sent Events
    # For now, we'll return stage information in the response
    
    stages = [
        {'stage': 1, 'name': 'Uploading Resume', 'status': 'completed'},
        {'stage': 2, 'name': 'Extracting Text', 'status': 'in_progress'},
        {'stage': 3, 'name': 'Analyzing Content', 'status': 'pending'},
        {'stage': 4, 'name': 'Generating Insights', 'status': 'pending'},
        {'stage': 5, 'name': 'Calculating Selection Chances', 'status': 'pending'}
    ]
    
    return jsonify({'stages': stages})

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    logger.info('Function [analyze_resume] called')
    
    if 'file' not in request.files:
        logger.warning('Function [analyze_resume] completed - No file provided')
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        logger.warning('Function [analyze_resume] completed - Empty filename')
        return jsonify({'error': 'Empty filename'}), 400

    # Get role and company from form data (optional)
    role = request.form.get('role', '').strip()
    company = request.form.get('company', '').strip()
    
    logger.info(f'Processing file: {file.filename}, role: {role or "Not specified"}, company: {company or "Not specified"}')
    text = extract_text_from_resume(file)
    if text.startswith("Unsupported"):
        logger.warning('Function [analyze_resume] completed - Unsupported file format')
        return jsonify({'error': text}), 400

    if not GEMINI_API_KEY:
        logger.error('Function [analyze_resume] completed - GEMINI_API_KEY not configured')
        return jsonify({'error': 'GEMINI_API_KEY not configured in .env'}), 500

    response = analyze_resume_with_gemini(text, GEMINI_API_KEY, role, company)
    if response.get('error'):
        logger.error(f'Function [analyze_resume] completed - Error: {response["error"]}')
        return jsonify({'error': response['error']}), 500
    
    # Save the resume and analysis with role and company
    save_last_resume(file.filename, text, response['content'], role, company)
    
    logger.info('Function [analyze_resume] completed successfully')
    return jsonify(response['content'])

if __name__ == '__main__':
    # Note: For real-time stage updates, consider using Flask-SocketIO
    app.run(debug=True, threaded=True)
