from flask import Flask, request, jsonify
from ki import NeoCortex
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
cortex = NeoCortex()

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

@app.route('/api/solve', methods=['POST'])
@require_api_key
def solve():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    show_work = data.get('show_work', True)
    use_agents = data.get('use_agents', True)
    
    try:
        result = cortex.solve(data['query'], show_work, use_agents)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/agents/status', methods=['GET'])
@require_api_key
def get_agent_status():
    if not hasattr(cortex, 'multi_agent_system'):
        return jsonify({'error': 'Multi-agent system not initialized'}), 404
    
    try:
        agent_status = cortex.multi_agent_system.get_agent_status()
        return jsonify(agent_status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fast-response', methods=['POST'])
@require_api_key
def fast_response():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query parameter'}), 400
    
    show_work = data.get('show_work', True)
    
    try:
        result = cortex._fast_response(data['query'], show_work)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 