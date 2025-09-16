from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from analysis_engine import run_bullish_analysis

def parse_analysis_result(result_text):
    """
    Parse the analysis result text into structured data for the UI.
    """
    lines = result_text.split('\n')
    
    summary_lines = []
    risk_lines = []
    pricing_lines = []
    top_5_data = []
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect sections
        if "TOP RECOMMENDED TRADE" in line.upper():
            current_section = "summary"
            continue
        elif "STRATEGY OVERVIEW" in line.upper() or "RISK" in line.upper():
            current_section = "risk"
            continue
        elif "PRICING COMPARISON" in line.upper():
            current_section = "pricing"
            continue
        elif "TOP 5 COMBINATIONS" in line.upper():
            current_section = "top5"
            continue
        elif "No valid strategies found" in line:
            return {
                "summary": "No valid strategies found for these parameters.",
                "risk": "",
                "pricing_comparison": "",
                "top_5": []
            }
        
        # Add lines to appropriate section
        if current_section == "summary":
            summary_lines.append(line)
        elif current_section == "risk":
            risk_lines.append(line)
        elif current_section == "pricing":
            pricing_lines.append(line)
        elif current_section == "top5":
            # Parse table data, skip header and separator lines
            if "|" in line and not line.startswith("---"):
                # Skip the header row
                if "RANK" in line.upper() and "EXPIRATION" in line.upper():
                    continue
                parts = [part.strip() for part in line.split("|") if part.strip()]
                if len(parts) >= 7:
                    top_5_data.append(tuple(parts[:7]))  # Rank, Expiration, Strikes, Net Cost, Net Vega, Efficiency, Score
    
    return {
        "summary": "\n".join(summary_lines),
        "risk": "\n".join(risk_lines),
        "pricing_comparison": "\n".join(pricing_lines),
        "top_5": top_5_data
    }

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Parse request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Extract parameters
            ticker = data.get('ticker', '').upper()
            min_dte = data.get('min_dte', 30)
            max_dte = data.get('max_dte', 90)
            
            # Validate input
            if not ticker:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Ticker symbol is required'}).encode())
                return
            
            # Run analysis
            result_text = run_bullish_analysis(ticker, min_dte, max_dte)
            parsed_result = parse_analysis_result(result_text)
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'result': parsed_result}).encode())
            
        except Exception as e:
            # Send error response
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            error_response = {
                'result': {
                    'summary': f"Analysis Error: {str(e)}",
                    'risk': "",
                    'pricing_comparison': "",
                    'top_5': []
                }
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
