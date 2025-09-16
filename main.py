from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import os
import subprocess
import threading
import time

# Import analysis engine
from api.analyze.analysis_engine import run_bullish_analysis, run_bearish_analysis

app = FastAPI()

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    ticker: str
    min_dte: int
    max_dte: int

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

@app.post("/api/analyze/bullish")
def analyze_bullish(req: AnalyzeRequest):
    try:
        result_text = run_bullish_analysis(req.ticker, req.min_dte, req.max_dte)
        parsed_result = parse_analysis_result(result_text)
        return {"result": parsed_result}
    except Exception as e:
        return {"result": {
            "summary": f"Analysis Error: {str(e)}",
            "risk": "",
            "pricing_comparison": "",
            "top_5": []
        }}

@app.post("/api/analyze/bearish")
def analyze_bearish(req: AnalyzeRequest):
    try:
        result_text = run_bearish_analysis(req.ticker, req.min_dte, req.max_dte)
        parsed_result = parse_analysis_result(result_text)
        return {"result": parsed_result}
    except Exception as e:
        return {"result": {
            "summary": f"Analysis Error: {str(e)}",
            "risk": "",
            "pricing_comparison": "",
            "top_5": []
        }}

@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "VegaEdge API is running"}

@app.get("/")
def serve_frontend():
    """Serve the Next.js frontend"""
    return FileResponse('out/index.html')

# Serve static files from Next.js build
if os.path.exists('out'):
    app.mount("/", StaticFiles(directory="out", html=True), name="static")

def build_frontend():
    """Build the Next.js frontend"""
    try:
        print("Building Next.js frontend...")
        subprocess.run(["npm", "install"], check=True)
        subprocess.run(["npm", "run", "build"], check=True)
        print("Frontend build completed!")
    except Exception as e:
        print(f"Frontend build failed: {e}")

if __name__ == "__main__":
    # Build frontend in background
    build_thread = threading.Thread(target=build_frontend)
    build_thread.daemon = True
    build_thread.start()
    
    # Start the server
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
