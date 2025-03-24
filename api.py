from flask import Flask, request, jsonify, Response
from ki import NeoCortex
from functools import wraps
from flask_cors import CORS
import json
import gzip
import logging
import re

# Configure detailed logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure the Together API is available
try:
    from together import Together
    logger.info("Together API imported successfully")
except ImportError:
    logger.error("Error importing Together API, please install with 'pip install together'")

app = Flask(__name__)
CORS(app)
# Create a NeoCortex instance with DeepSeek V3 model
cortex = NeoCortex(model_name="deepseek-ai/DeepSeek-V3")

# Helper function to get current timestamp
def import_time():
    from datetime import datetime
    return datetime.now().isoformat()

# Increase Flask's maximum response size and timeouts
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Disable pretty printing to save space

# API key for authentication
API_KEY = "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"

# Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for API key in headers or query parameters
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized: Invalid or missing API key'}), 401
        
        return f(*args, **kwargs)
    return decorated

# Helper function to ensure complete responses
def ensure_complete_response(result):
    # Check if final_answer exists and might be truncated
    if 'final_answer' in result and isinstance(result['final_answer'], str):
        logger.info(f"Response length: {len(result['final_answer'])} characters")
        
        text = result['final_answer']
        
        # Don't flag well-formatted lists as truncated
        is_complete_list = bool(re.search(r'(\d+\.\s+.+\n)+\d+\.\s+.+[.!?]$', text)) or \
                           bool(re.search(r'(\*\s+.+\n)+\*\s+.+[.!?]$', text))
        
        # Check for specific signs of truncation
        has_truncation_signs = text.endswith('...') or \
                               (re.search(r'\w+$', text) and not re.search(r'[.!?;:]$', text) and \
                                not re.search(r'^\d+\.\s+.+$', text.split('\n')[-1].strip()))
        
        # Check for conclusion markers that indicate a complete response
        has_conclusion = re.search(r'hope\s+this\s+(helps|is\s+helpful)', text, re.I) or \
                         re.search(r'let\s+me\s+know\s+if', text, re.I) or \
                         re.search(r'thanks|thank\s+you', text, re.I) or \
                         re.search(r'in\s+summary|in\s+conclusion|to\s+summarize', text, re.I)
        
        if has_truncation_signs and not is_complete_list and not has_conclusion:
            logger.warning("Response appears to be truncated, marking for client-side handling")
            result['_may_be_truncated'] = True
        else:
            logger.info("Response appears to be complete")
    
    # Compress large responses if needed
    should_compress = False
    result_json = json.dumps(result, ensure_ascii=False)
    response_size = len(result_json.encode('utf-8'))
    
    logger.info(f"Total response size: {response_size / 1024:.2f} KB")
    
    if response_size > 10 * 1024 * 1024:  # If larger than 10MB
        should_compress = True
        logger.info("Large response detected, using compression")
    
    # Ensure safe JSON serialization without truncation
    try:
        if should_compress:
            # Compress the response
            compressed_data = gzip.compress(result_json.encode('utf-8'))
            response = Response(compressed_data)
            response.headers['Content-Encoding'] = 'gzip'
            response.headers['Content-Type'] = 'application/json'
            response.headers['X-Response-Size'] = str(response_size)
            return response
        else:
            # Use direct response without compression for smaller payloads
            response = Response(
                response=result_json,
                status=200,
                mimetype='application/json'
            )
            response.headers['X-Response-Size'] = str(response_size)
            return response
    except Exception as e:
        logger.error(f"JSON serialization error: {str(e)}")
        return jsonify({'error': 'Failed to serialize response', 'details': str(e)}), 500

@app.route('/api/solve', methods=['POST'])
@require_api_key
def solve():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    show_work = data.get('show_work', True)
    use_agents = data.get('use_agents', True)
    
    logger.info(f"Processing query: {data['query'][:50]}... (show_work={show_work}, use_agents={use_agents})")
    
    try:
        result = cortex.solve(data['query'], show_work, use_agents)
        
        # Ensure reasoning_process is included but not so large that it causes truncation
        if 'reasoning_process' in result:
            logger.info("Reasoning process included in response")
        
        # Add safety metadata for client
        result['_api_version'] = "1.0.1"
        result['_timestamp'] = import_time()
        
        return ensure_complete_response(result)
    except AttributeError as e:
        if 'context_window_manager' in str(e):
            # Handle the specific missing attribute error
            error_msg = "Missing 'context_window_manager' in NeoCortex. Please add this attribute to your NeoCortex class in ki.py."
            logger.error(f"API Error: {error_msg}")
            return jsonify({'error': error_msg}), 500
        # Other attribute errors
        logger.error(f"API AttributeError: {str(e)}")
        return jsonify({'error': f"AttributeError: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/status', methods=['GET'])
@require_api_key
def get_agent_status():
    if not hasattr(cortex, 'multi_agent_system'):
        return jsonify({'error': 'Multi-agent system not initialized'}), 404
    
    try:
        agent_status = cortex.multi_agent_system.get_agent_status()
        return ensure_complete_response(agent_status)
    except AttributeError as e:
        if 'context_window_manager' in str(e):
            # Handle the specific missing attribute error
            error_msg = "Missing 'context_window_manager' in NeoCortex. Please add this attribute to your NeoCortex class in ki.py."
            logger.error(f"API Error: {error_msg}")
            return jsonify({'error': error_msg}), 500
        # Other attribute errors
        logger.error(f"API AttributeError: {str(e)}")
        return jsonify({'error': f"AttributeError: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fast-response', methods=['POST'])
@require_api_key
def fast_response():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    show_work = data.get('show_work', True)
    
    logger.info(f"Processing fast query: {data['query'][:50]}... (show_work={show_work})")
    
    try:
        result = cortex._fast_response(data['query'], show_work)
        
        # Add safety metadata for client
        result['_api_version'] = "1.0.1"
        result['_timestamp'] = import_time()
        
        return ensure_complete_response(result)
    except AttributeError as e:
        if 'context_window_manager' in str(e):
            # Handle the specific missing attribute error
            error_msg = "Missing 'context_window_manager' in NeoCortex. Please add this attribute to your NeoCortex class in ki.py."
            logger.error(f"API Error: {error_msg}")
            return jsonify({'error': error_msg}), 500
        # Other attribute errors
        logger.error(f"API AttributeError: {str(e)}")
        return jsonify({'error': f"AttributeError: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True, processes=1) 