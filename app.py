from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "api_name": "Pakistan Number Info API",
        "version": "1.0",
        "status": "active",
        "endpoints": {
            "/search": {
                "method": "POST",
                "usage": '{"query": "03123456789"}',
                "example": 'curl -X POST https://yourapi.railway.app/search -H "Content-Type: application/json" -d \'{"query": "3359736848"}\''
            },
            "/search?query=number": {
                "method": "GET",
                "usage": "https://yourapi.railway.app/search?query=3359736848",
                "example": "Open in browser"
            }
        },
        "supported_queries": [
            "Mobile Number: 10-11 digits (e.g., 3359736848)",
            "CNIC: 13 digits (e.g., 2150952917167)",
            "Mobile with 0: (e.g., 03123456789)"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/search', methods=['POST', 'GET'])
def search():
    """Main search endpoint - returns COMPLETE response"""
    try:
        # Get query from request
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
                query = data.get('query', '').strip()
            else:
                query = request.form.get('query', '').strip()
        else:  # GET method
            query = request.args.get('query', '').strip()
        
        # Validate query
        if not query:
            return jsonify({
                "success": False,
                "error": "Query is required",
                "example": {"query": "3359736848"}
            }), 400
        
        # Clean query (keep only numbers)
        query = ''.join(filter(str.isdigit, query))
        
        if len(query) < 10:
            return jsonify({
                "success": False,
                "error": "Invalid length. Must be at least 10 digits for mobile or 13 for CNIC",
                "your_query": query,
                "length": len(query)
            }), 400
        
        print(f"[{datetime.now()}] Searching for: {query}")
        
        # Prepare API request to external service
        api_url = 'https://simownership.com/wp-admin/admin-ajax.php'
        
        payload = {
            'post_id': '413',
            'form_id': '5e17544',
            'referer_title': 'Search SIM and CNIC Details',
            'queried_id': '413',
            'form_fields[search]': query,
            'action': 'elementor_pro_forms_send_form',
            'referrer': 'https://simownership.com/search/'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://simownership.com',
            'Referer': 'https://simownership.com/search/',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        # Make the API call
        response = requests.post(api_url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            # Get FULL response from external API
            full_response = response.json()
            
            # Create our response with ALL data
            result = {
                "request_info": {
                    "your_query": query,
                    "query_type": "mobile" if len(query) in [10, 11] else "cnic",
                    "timestamp": datetime.now().isoformat(),
                    "status_code": response.status_code
                },
                "api_response": full_response  # This contains ALL data from external API
            }
            
            # Add simplified results if available
            if full_response.get('success') and full_response.get('data', {}).get('data', {}).get('results'):
                results = full_response['data']['data']['results']
                
                # Extract and format individual results
                formatted_results = []
                for idx, item in enumerate(results, 1):
                    formatted_results.append({
                        "result_id": idx,
                        "mobile_number": item.get('n', 'N/A'),
                        "name": item.get('name', 'N/A'),
                        "father_name": item.get('father_name', 'N/A'),
                        "cnic": item.get('cnic', 'N/A'),
                        "address": item.get('address', 'N/A'),
                        "network": item.get('network', 'N/A'),
                        "registration_date": item.get('registration_date', 'N/A'),
                        "family_members": item.get('family_members', 'N/A'),
                        "other_numbers": item.get('other_numbers', 'N/A')
                    })
                
                result["summary"] = {
                    "total_results": len(results),
                    "results": formatted_results
                }
            
            return jsonify(result)
            
        else:
            return jsonify({
                "success": False,
                "error": f"External API error: {response.status_code}",
                "your_query": query,
                "timestamp": datetime.now().isoformat()
            }), 502
            
    except requests.exceptions.Timeout:
        return jsonify({
            "success": False,
            "error": "Request timeout. Service is taking too long to respond.",
            "your_query": query,
            "timestamp": datetime.now().isoformat()
        }), 504
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint with sample data"""
    return jsonify({
        "message": "API is working!",
        "sample_queries": [
            "https://yourapi.railway.app/search?query=3359736848",
            "https://yourapi.railway.app/search?query=2150952917167"
        ],
        "sample_post_request": {
            "curl_command": 'curl -X POST https://yourapi.railway.app/search -H "Content-Type: application/json" -d \'{"query": "3359736848"}\''
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)