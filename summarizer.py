import pdfplumber
import requests
import json
import logging
import time

logger = logging.getLogger(__name__)

def extract_text_from_resume(file):
    logger.info(f'Function [extract_text_from_resume] called for file: {file.filename}')
    
    if file.filename.endswith('.txt'):
        text = file.read().decode('utf-8')
        logger.info(f'Function [extract_text_from_resume] completed - Extracted {len(text)} characters from TXT')
        return text
    elif file.filename.endswith('.pdf'):
        # Use pdfplumber to open and read the PDF
        with pdfplumber.open(file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            logger.info(f'Function [extract_text_from_resume] completed - Extracted {len(text)} characters from PDF')
            return text
    else:
        logger.warning('Function [extract_text_from_resume] completed - Unsupported file format')
        return "Unsupported file format."

def analyze_resume_with_gemini(text, api_key, role='', company=''):
    """Call Google Gemini API directly via REST to analyze resume text."""
    logger.info(f'Function [analyze_resume_with_gemini] called with text length: {len(text)}, role: {role or "unspecified"}, company: {company or "unspecified"}')
    
    # Use only gemini-2.5-flash model
    model = 'gemini-2.0-flash'
    
    # Build dynamic prompt based on role and company
    if role and company:
        prompt = f"""
Analyze the following resume for a {role} position at {company}.

Provide a detailed analysis in JSON format with the following structure:
{{
  "summary": "Brief 2-3 sentence summary of the candidate",
  "strengths": ["list of key strengths relevant to {role} at {company}"],
  "shortcomings": ["specific weaknesses or missing skills for {role} at {company}"],
  "selection_chance": "percentage (e.g., 75%)",
  "selection_reasoning": "Detailed explanation of why this percentage, what increases/decreases chances",
  "recommendations": ["specific actionable improvements for {role} at {company}"]
}}

Resume text:
{text}
"""
    elif role:
        prompt = f"""
Analyze the following resume for a {role} position.

Provide a detailed analysis in JSON format with the following structure:
{{
  "summary": "Brief 2-3 sentence summary of the candidate",
  "strengths": ["list of key strengths relevant to {role}"],
  "shortcomings": ["specific weaknesses or missing skills for {role}"],
  "recommended_companies": ["companies that would be a good fit based on the profile"],
  "selection_chance": "percentage for typical {role} positions (e.g., 70%)",
  "selection_reasoning": "Detailed explanation of the percentage",
  "recommendations": ["specific actionable improvements for {role}"]
}}

Resume text:
{text}
"""
    elif company:
        prompt = f"""
Analyze the following resume for positions at {company}.

Provide a detailed analysis in JSON format with the following structure:
{{
  "summary": "Brief 2-3 sentence summary of the candidate",
  "strengths": ["list of key strengths relevant to {company}"],
  "shortcomings": ["specific weaknesses or missing skills for {company}"],
  "recommended_roles": ["roles at {company} that would be a good fit"],
  "selection_chance": "percentage for positions at {company} (e.g., 65%)",
  "selection_reasoning": "Detailed explanation of the percentage",
  "recommendations": ["specific actionable improvements for {company}"]
}}

Resume text:
{text}
"""
    else:
        prompt = f"""
Analyze the following resume and provide comprehensive career guidance.

Provide a detailed analysis in JSON format with the following structure:
{{
  "summary": "Brief 2-3 sentence summary of the candidate",
  "strengths": ["list of key strengths"],
  "shortcomings": ["areas for improvement"],
  "recommended_roles": ["3-5 specific roles that would be a best fit based on skills and experience"],
  "recommended_companies": ["5-8 specific company names (like Google, Amazon, Microsoft, etc.) that match the profile and experience level"],
  "roadmap": {{
    "short_term": ["2-3 actionable steps to take in the next 1-3 months"],
    "mid_term": ["2-3 goals to achieve in the next 3-6 months"],
    "long_term": ["2-3 strategic objectives for 6-12 months"]
  }},
  "overall_assessment": "General assessment of career readiness and marketability",
  "recommendations": ["specific actionable improvements for career growth"]
}}

Resume text:
{text}
"""
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.0
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Use gemini-2.5-flash with retry logic
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    logger.info(f'Using model: {model}')
    
    # Retry logic: 3 attempts with exponential backoff
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.info(f'Sending request to Gemini API (attempt {attempt + 1}/{max_retries})')
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            
            # If successful, process response
            if response.status_code == 200:
                result = response.json()
                # Extract the generated text from the response
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    logger.info(f'Function [analyze_resume_with_gemini] completed successfully with {model} - Generated {len(content)} characters')
                    
                    # Try to parse as JSON, fallback to raw content
                    try:
                        # Clean markdown code blocks if present
                        cleaned = content.strip()
                        if cleaned.startswith('```json'):
                            cleaned = cleaned[7:]
                        if cleaned.startswith('```'):
                            cleaned = cleaned[3:]
                        if cleaned.endswith('```'):
                            cleaned = cleaned[:-3]
                        parsed = json.loads(cleaned.strip())
                        return {'content': parsed, 'raw': content}
                    except json.JSONDecodeError:
                        logger.warning('Response is not valid JSON, returning as raw text')
                        return {'content': {'raw_analysis': content}, 'raw': content}
                else:
                    logger.error(f'No content returned from Gemini API with {model}')
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return {'error': f'No content returned from {model}'}
            
            # If 503 (service unavailable) or 429 (rate limit), retry with backoff
            elif response.status_code in [503, 429]:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f'Model {model} returned {response.status_code}, retrying in {wait_time}s...')
                    time.sleep(wait_time)
                    continue
                else:
                    logger.warning(f'Model {model} failed after {max_retries} attempts with status {response.status_code}')
                    return {'error': f'{model} returned status {response.status_code}'}
            
            # For other errors, return error
            else:
                logger.warning(f'Model {model} returned status {response.status_code}: {response.text[:200]}')
                if attempt < max_retries - 1:
                    continue
                else:
                    return {'error': f'{model} returned status {response.status_code}'}
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 1
                logger.warning(f'Request timeout with {model}, retrying in {wait_time}s...')
                time.sleep(wait_time)
                continue
            else:
                logger.error(f'Request timeout with {model} after {max_retries} attempts')
                return {'error': f'Request timeout with {model}'}
                
        except requests.exceptions.RequestException as e:
            logger.error(f'Request exception with {model}: {str(e)}')
            return {'error': f'Request exception: {str(e)}'}
        except (KeyError, IndexError) as e:
            logger.error(f'Failed to parse API response from {model}: {str(e)}')
            return {'error': f'Failed to parse response: {str(e)}'}
    
    # If all retries failed
    logger.error('Function [analyze_resume_with_gemini] completed - All attempts failed')
    return {'error': 'Gemini API is currently unavailable. Please try again in a few moments.'}
