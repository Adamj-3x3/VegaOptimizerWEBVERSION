from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import os

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
    """Parse the analysis result text into structured data for the UI."""
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
    """Serve a simple HTML frontend"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>VegaEdge Option Strategy Analyzer</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
        <div class="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
            <!-- Header -->
            <header class="bg-black/20 backdrop-blur-sm border-b border-blue-500/20">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex items-center justify-between h-16">
                        <div class="flex items-center space-x-3">
                            <div class="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                                <span class="text-white font-bold text-sm">VE</span>
                            </div>
                            <h1 class="text-xl font-bold text-white">VegaEdge</h1>
                            <span class="text-blue-300 text-sm">Option Strategy Analyzer</span>
                        </div>
                        <div class="text-blue-300 text-sm">
                            Professional Options Analysis
                        </div>
                    </div>
                </div>
            </header>

            <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <!-- Input Form -->
                <div class="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6 mb-8">
                    <h2 class="text-2xl font-bold text-white mb-6">Analysis Parameters</h2>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <!-- Ticker Input -->
                        <div>
                            <label class="block text-blue-300 text-sm font-medium mb-2">
                                Ticker Symbol
                            </label>
                            <input
                                type="text"
                                id="ticker"
                                placeholder="e.g., AAPL"
                                class="w-full px-3 py-2 bg-white/10 border border-blue-500/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <!-- Min DTE -->
                        <div>
                            <label class="block text-blue-300 text-sm font-medium mb-2">
                                Min Days to Expiry
                            </label>
                            <input
                                type="number"
                                id="minDte"
                                value="30"
                                min="1"
                                max="365"
                                class="w-full px-3 py-2 bg-white/10 border border-blue-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <!-- Max DTE -->
                        <div>
                            <label class="block text-blue-300 text-sm font-medium mb-2">
                                Max Days to Expiry
                            </label>
                            <input
                                type="number"
                                id="maxDte"
                                value="90"
                                min="1"
                                max="365"
                                class="w-full px-3 py-2 bg-white/10 border border-blue-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                        </div>

                        <!-- Strategy Type -->
                        <div>
                            <label class="block text-blue-300 text-sm font-medium mb-2">
                                Strategy Type
                            </label>
                            <select
                                id="strategyType"
                                class="w-full px-3 py-2 bg-white/10 border border-blue-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="bullish">Bullish</option>
                                <option value="bearish">Bearish</option>
                            </select>
                        </div>
                    </div>

                    <div class="flex space-x-4 mt-6">
                        <button
                            id="analyzeBtn"
                            class="px-6 py-3 bg-gradient-to-r from-blue-500 to-green-500 text-white font-semibold rounded-lg hover:from-blue-600 hover:to-green-600 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                            Run Analysis
                        </button>
                        <button
                            id="clearBtn"
                            class="px-6 py-3 bg-gray-600 text-white font-semibold rounded-lg hover:bg-gray-700 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500"
                        >
                            Clear Results
                        </button>
                    </div>
                </div>

                <!-- Results -->
                <div id="results" class="hidden">
                    <div class="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6">
                        <h2 class="text-2xl font-bold text-white mb-6">Analysis Results</h2>
                        <div id="resultContent" class="text-white"></div>
                    </div>
                </div>

                <!-- Loading -->
                <div id="loading" class="hidden text-center py-8">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <p class="text-blue-300 mt-2">Analyzing options...</p>
                </div>
            </main>
        </div>

        <script>
            const analyzeBtn = document.getElementById('analyzeBtn');
            const clearBtn = document.getElementById('clearBtn');
            const results = document.getElementById('results');
            const loading = document.getElementById('loading');
            const resultContent = document.getElementById('resultContent');

            analyzeBtn.addEventListener('click', async () => {
                const ticker = document.getElementById('ticker').value.trim();
                const minDte = parseInt(document.getElementById('minDte').value);
                const maxDte = parseInt(document.getElementById('maxDte').value);
                const strategyType = document.getElementById('strategyType').value;

                if (!ticker) {
                    alert('Please enter a ticker symbol');
                    return;
                }

                // Show loading
                loading.classList.remove('hidden');
                results.classList.add('hidden');

                try {
                    const response = await fetch(`/api/analyze/${strategyType}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            ticker: ticker.toUpperCase(),
                            min_dte: minDte,
                            max_dte: maxDte,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }

                    const data = await response.json();
                    displayResults(data.result);
                } catch (error) {
                    displayError(error.message);
                } finally {
                    loading.classList.add('hidden');
                }
            });

            clearBtn.addEventListener('click', () => {
                results.classList.add('hidden');
                resultContent.innerHTML = '';
            });

            function displayResults(result) {
                let html = '';
                
                if (result.summary) {
                    html += `<div class="mb-6"><h3 class="text-lg font-semibold text-green-400 mb-2">Summary</h3><pre class="text-sm text-gray-300 whitespace-pre-wrap">${result.summary}</pre></div>`;
                }
                
                if (result.risk) {
                    html += `<div class="mb-6"><h3 class="text-lg font-semibold text-yellow-400 mb-2">Risk Analysis</h3><pre class="text-sm text-gray-300 whitespace-pre-wrap">${result.risk}</pre></div>`;
                }
                
                if (result.top_5 && result.top_5.length > 0) {
                    html += `<div class="mb-6"><h3 class="text-lg font-semibold text-blue-400 mb-2">Top Recommendations</h3>`;
                    html += `<div class="overflow-x-auto"><table class="min-w-full text-sm text-gray-300">`;
                    html += `<thead><tr class="border-b border-gray-600"><th class="px-4 py-2 text-left">Rank</th><th class="px-4 py-2 text-left">Expiration</th><th class="px-4 py-2 text-left">Strikes</th><th class="px-4 py-2 text-left">Net Cost</th><th class="px-4 py-2 text-left">Net Vega</th><th class="px-4 py-2 text-left">Efficiency</th><th class="px-4 py-2 text-left">Score</th></tr></thead>`;
                    html += `<tbody>`;
                    result.top_5.forEach(row => {
                        html += `<tr class="border-b border-gray-700"><td class="px-4 py-2">${row[0]}</td><td class="px-4 py-2">${row[1]}</td><td class="px-4 py-2">${row[2]}</td><td class="px-4 py-2">${row[3]}</td><td class="px-4 py-2">${row[4]}</td><td class="px-4 py-2">${row[5]}</td><td class="px-4 py-2">${row[6]}</td></tr>`;
                    });
                    html += `</tbody></table></div></div>`;
                }

                resultContent.innerHTML = html;
                results.classList.remove('hidden');
            }

            function displayError(message) {
                resultContent.innerHTML = `<div class="text-red-400"><h3 class="text-lg font-semibold mb-2">Error</h3><p>${message}</p></div>`;
                results.classList.remove('hidden');
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
