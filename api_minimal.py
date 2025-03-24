from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import logging
import re
from together import Together

# Configure detailed logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Helper function to get current timestamp
def import_time():
    from datetime import datetime
    return datetime.now().isoformat()

# API key for authentication
API_KEY = "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"
TOGETHER_API_KEY = "3405ce428ec69a2cf4c9f128064e9bc367b630fafc5968d2eff6bbdfaa462067"

# Authentication decorator
def require_api_key(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for API key in headers or query parameters
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized: Invalid or missing API key'}), 401
        
        return f(*args, **kwargs)
    return decorated

# Simple AI client using Together API
class SimpleAIClient:
    def __init__(self, model_name="deepseek-ai/DeepSeek-V3"):
        self.model_name = model_name
        self.together_client = Together(api_key=TOGETHER_API_KEY)
        
    def generate_response(self, prompt, system_prompt=None):
        """Generate a response using the Together API."""
        try:
            # Default system prompt if none provided
            if system_prompt is None:
                system_prompt = """You are an advanced reasoning AI assistant with exceptional problem-solving abilities.
Be methodical and clear in your thinking. Avoid redundancy, and strive for precision.
Share your reasoning process explicitly and provide your final answers clearly."""
                
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.together_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=4000
            )
            
            if response and response.choices:
                return response.choices[0].message.content
            else:
                return "No response received from the model."
                
        except Exception as e:
            logger.error(f"Error in generate_response: {str(e)}")
            return f"Error: {str(e)}"

# Initialize the AI client
ai_client = SimpleAIClient(model_name="deepseek-ai/DeepSeek-V3")

@app.route('/api/solve', methods=['POST'])
@require_api_key
def solve():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    logger.info(f"Processing query: {data['query'][:50]}...")
    
    try:
        prompt = f"""
        Please solve the following problem:
        
        {data['query']}
        
        Provide a clear and comprehensive solution.
        """
        
        result = ai_client.generate_response(prompt)
        
        response = {
            'final_answer': result,
            '_api_version': "1.0.1",
            '_timestamp': import_time()
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fast-response', methods=['POST'])
@require_api_key
def fast_response():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    logger.info(f"Processing fast query: {data['query'][:50]}...")
    
    try:
        prompt = f"""Provide a direct, efficient answer to this question: {data['query']}

If the question is straightforward, just give the answer without elaborate explanation.
If the question requires some reasoning, briefly show your work.
"""
        
        result = ai_client.generate_response(prompt)
        
        response = {
            'final_answer': result,
            '_api_version': "1.0.1",
            '_timestamp': import_time()
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 