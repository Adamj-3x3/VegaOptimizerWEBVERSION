import { useState } from 'react';
import Head from 'next/head';

interface AnalysisResult {
  summary: string;
  risk: string;
  pricing_comparison: string;
  top_5: Array<[string, string, string, string, string, string, string]>;
}

export default function Home() {
  const [ticker, setTicker] = useState('');
  const [minDte, setMinDte] = useState(30);
  const [maxDte, setMaxDte] = useState(90);
  const [strategyType, setStrategyType] = useState<'bullish' | 'bearish'>('bullish');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!ticker.trim()) {
      setError('Please enter a ticker symbol');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

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
      setResult(data.result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during analysis');
    } finally {
      setIsLoading(false);
    }
  };

  const clearResults = () => {
    setResult(null);
    setError(null);
  };

  return (
    <>
      <Head>
        <title>VegaEdge - Option Strategy Analyzer</title>
        <meta name="description" content="Professional options analysis and strategy recommendations" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
        {/* Header */}
        <header className="bg-black/20 backdrop-blur-sm border-b border-blue-500/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-green-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">VE</span>
                </div>
                <h1 className="text-xl font-bold text-white">VegaEdge</h1>
                <span className="text-blue-300 text-sm">Option Strategy Analyzer</span>
              </div>
              <div className="text-blue-300 text-sm">
                Professional Options Analysis
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Input Form */}
          <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6 mb-8">
            <h2 className="text-2xl font-bold text-white mb-6">Analysis Parameters</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {/* Ticker Input */}
              <div>
                <label className="block text-blue-300 text-sm font-medium mb-2">
                  Ticker Symbol
                </label>
                <input
                  type="text"
                  value={ticker}
                  onChange={(e) => setTicker(e.target.value.toUpperCase())}
                  placeholder="e.g., AAPL"
                  className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Min DTE */}
              <div>
                <label className="block text-blue-300 text-sm font-medium mb-2">
                  Min Days to Expiry
                </label>
                <input
                  type="number"
                  value={minDte}
                  onChange={(e) => setMinDte(parseInt(e.target.value) || 0)}
                  min="1"
                  className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Max DTE */}
              <div>
                <label className="block text-blue-300 text-sm font-medium mb-2">
                  Max Days to Expiry
                </label>
                <input
                  type="number"
                  value={maxDte}
                  onChange={(e) => setMaxDte(parseInt(e.target.value) || 0)}
                  min="1"
                  className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Strategy Type */}
              <div>
                <label className="block text-blue-300 text-sm font-medium mb-2">
                  Strategy Type
                </label>
                <select
                  value={strategyType}
                  onChange={(e) => setStrategyType(e.target.value as 'bullish' | 'bearish')}
                  className="w-full px-4 py-3 bg-slate-800/50 border border-blue-500/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="bullish">Bullish</option>
                  <option value="bearish">Bearish</option>
                </select>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4 mt-6">
              <button
                onClick={handleAnalyze}
                disabled={isLoading}
                className="px-8 py-3 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-all duration-200 flex items-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <span>Run Analysis</span>
                )}
              </button>
              
              <button
                onClick={clearResults}
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-white font-medium rounded-lg transition-colors duration-200"
              >
                Clear Results
              </button>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2">
                <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">!</span>
                </div>
                <span className="text-red-300">{error}</span>
              </div>
            </div>
          )}

          {/* Results Display */}
          {result && (
            <div className="space-y-6">
              {/* Summary */}
              {result.summary && (
                <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6">
                  <h3 className="text-xl font-bold text-white mb-4">Top Recommended Trade</h3>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <pre className="text-green-300 whitespace-pre-wrap font-mono text-sm">{result.summary}</pre>
                  </div>
                </div>
              )}

              {/* Risk Analysis */}
              {result.risk && (
                <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6">
                  <h3 className="text-xl font-bold text-white mb-4">Strategy Overview & Risk</h3>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <pre className="text-blue-300 whitespace-pre-wrap font-mono text-sm">{result.risk}</pre>
                  </div>
                </div>
              )}

              {/* Pricing Comparison */}
              {result.pricing_comparison && (
                <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6">
                  <h3 className="text-xl font-bold text-white mb-4">Pricing Comparison</h3>
                  <div className="bg-slate-800/50 rounded-lg p-4">
                    <pre className="text-yellow-300 whitespace-pre-wrap font-mono text-sm">{result.pricing_comparison}</pre>
                  </div>
                </div>
              )}

              {/* Top 5 Combinations */}
              {result.top_5 && result.top_5.length > 0 && (
                <div className="bg-white/5 backdrop-blur-sm rounded-xl border border-blue-500/20 p-6">
                  <h3 className="text-xl font-bold text-white mb-4">Top 5 Combinations</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full bg-slate-800/50 rounded-lg">
                      <thead>
                        <tr className="border-b border-slate-700">
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Rank</th>
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Expiration</th>
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Strikes</th>
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Net Cost</th>
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Net Vega</th>
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Efficiency</th>
                          <th className="px-4 py-3 text-left text-blue-300 font-medium">Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.top_5.map((row, index) => (
                          <tr key={index} className="border-b border-slate-700/50 last:border-b-0">
                            {row.map((cell, cellIndex) => (
                              <td key={cellIndex} className="px-4 py-3 text-white font-mono text-sm">
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </>
  );
}
