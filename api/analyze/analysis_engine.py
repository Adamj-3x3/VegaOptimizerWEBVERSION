import yfinance as yf
import json
import math
from datetime import datetime
import time

# Lightweight analysis engine with minimal dependencies
def normal_cdf(x):
    """Approximate normal CDF using error function"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def normal_pdf(x):
    """Normal PDF"""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)

def d1(S, K, T, r, sigma, q=0.0):
    if T <= 0 or sigma <= 0: 
        return float('inf') if S > K else float('-inf')
    return (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))

def d2(S, K, T, r, sigma, q=0.0):
    return d1(S, K, T, r, sigma, q) - sigma * math.sqrt(T)

def bs_vega(S, K, T, r, sigma, q=0.0):
    if T <= 0 or sigma <= 0: 
        return 0
    D1 = d1(S, K, T, r, sigma, q)
    return S * math.exp(-q * T) * normal_pdf(D1) * math.sqrt(T) / 100

def bs_delta(S, K, T, r, sigma, option_type='call', q=0.0):
    if T <= 0: 
        return 1.0 if S > K and option_type == 'call' else (-1.0 if S < K and option_type == 'put' else 0.0)
    D1 = d1(S, K, T, r, sigma, q)
    return math.exp(-q * T) * normal_cdf(D1) if option_type == 'call' else math.exp(-q * T) * (normal_cdf(D1) - 1)

def get_options_data(ticker, expiration, underlying_price):
    try:
        stock = yf.Ticker(ticker)
        opt_chain = stock.option_chain(expiration)
    except Exception as e:
        return [], []

    def process_options(options_data):
        if options_data is None or len(options_data) == 0:
            return []
        
        valid_options = []
        for index in range(len(options_data)):
            try:
                option = options_data.iloc[index]
                # Check if required fields exist and are valid
                implied_vol = option.get('impliedVolatility')
                bid = option.get('bid', 0)
                ask = option.get('ask', 0)
                
                if (implied_vol is None or implied_vol <= 0.01 or
                    bid is None or bid <= 0 or
                    ask is None or ask <= 0):
                    continue
                
                # Check volume or open interest
                volume = option.get('volume', 0)
                open_interest = option.get('openInterest', 0)
                if volume <= 0 and open_interest <= 0:
                    continue
                
                # Check bid-ask spread
                if ask <= 0 or (ask - bid) / ask >= 0.6:
                    continue
                
                valid_options.append({
                    'strike': option.get('strike', 0),
                    'bid': bid,
                    'ask': ask,
                    'impliedVolatility': implied_vol,
                    'volume': volume,
                    'openInterest': open_interest
                })
            except Exception as e:
                continue
        
        return valid_options

    calls = process_options(opt_chain.calls)
    puts = process_options(opt_chain.puts)
    
    time.sleep(0.2)  # Be respectful to API
    return calls, puts

def analyze_bullish_risk_reversal(calls, puts, underlying_price, expiration_date, risk_free_rate=0.045):
    today = datetime.now().date()
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
    T = max((exp_date - today).days / 365.0, 1 / (365 * 24))
    days_to_exp = (exp_date - today).days

    # Calculate Greeks for each option
    for call in calls:
        call['vega'] = bs_vega(underlying_price, call['strike'], T, risk_free_rate, call['impliedVolatility'])
        call['delta'] = bs_delta(underlying_price, call['strike'], T, risk_free_rate, call['impliedVolatility'], 'call')
    
    for put in puts:
        put['vega'] = bs_vega(underlying_price, put['strike'], T, risk_free_rate, put['impliedVolatility'])
        put['delta'] = bs_delta(underlying_price, put['strike'], T, risk_free_rate, put['impliedVolatility'], 'put')

    # Filter OTM options
    otm_calls = [c for c in calls if c['strike'] > underlying_price]
    otm_puts = [p for p in puts if p['strike'] < underlying_price]

    max_strike_distance = underlying_price * 0.75
    otm_calls = [c for c in otm_calls if c['strike'] < underlying_price + max_strike_distance]
    otm_puts = [p for p in otm_puts if p['strike'] > underlying_price - max_strike_distance]

    if not otm_calls or not otm_puts:
        return []

    combinations = []
    for call in otm_calls:
        for put in otm_puts:
            if call['strike'] <= put['strike']:
                continue
            
            net_cost = call['ask'] - put['bid']
            strike_diff = call['strike'] - put['strike']
            efficiency = -net_cost / strike_diff if strike_diff > 0 else 0
            
            if abs(net_cost) > 20:
                continue
            
            net_delta = call['delta'] - put['delta']
            net_vega = call['vega'] - put['vega']
            
            if net_delta <= 0.1 or net_vega <= 0:
                continue
            
            combinations.append({
                'long_call_strike': call['strike'],
                'short_put_strike': put['strike'],
                'net_cost': net_cost,
                'net_delta': net_delta,
                'net_vega': net_vega,
                'efficiency': efficiency,
                'breakeven': call['strike'] + net_cost,
                'expiration': expiration_date,
                'days_to_exp': days_to_exp
            })
    
    return combinations

def analyze_bearish_risk_reversal(calls, puts, underlying_price, expiration_date, risk_free_rate=0.045):
    today = datetime.now().date()
    exp_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
    T = max((exp_date - today).days / 365.0, 1 / (365 * 24))
    days_to_exp = (exp_date - today).days

    # Calculate Greeks for each option
    for call in calls:
        call['vega'] = bs_vega(underlying_price, call['strike'], T, risk_free_rate, call['impliedVolatility'])
        call['delta'] = bs_delta(underlying_price, call['strike'], T, risk_free_rate, call['impliedVolatility'], 'call')
    
    for put in puts:
        put['vega'] = bs_vega(underlying_price, put['strike'], T, risk_free_rate, put['impliedVolatility'])
        put['delta'] = bs_delta(underlying_price, put['strike'], T, risk_free_rate, put['impliedVolatility'], 'put')

    # Filter OTM options
    otm_calls = [c for c in calls if c['strike'] > underlying_price]
    otm_puts = [p for p in puts if p['strike'] < underlying_price]

    max_strike_distance = underlying_price * 0.75
    otm_calls = [c for c in otm_calls if c['strike'] < underlying_price + max_strike_distance]
    otm_puts = [p for p in otm_puts if p['strike'] > underlying_price - max_strike_distance]

    if not otm_calls or not otm_puts:
        return []

    combinations = []
    for put in otm_puts:
        for call in otm_calls:
            if put['strike'] >= call['strike']:
                continue
            
            net_cost = put['ask'] - call['bid']
            strike_diff = call['strike'] - put['strike']
            efficiency = -net_cost / strike_diff if strike_diff > 0 else 0
            
            if abs(net_cost) > 20:
                continue
            
            net_delta = put['delta'] - call['delta']
            net_vega = put['vega'] - call['vega']
            
            if net_delta >= -0.1 or net_vega > 0.01:
                continue
            
            combinations.append({
                'long_put_strike': put['strike'],
                'short_call_strike': call['strike'],
                'net_cost': net_cost,
                'net_delta': net_delta,
                'net_vega': net_vega,
                'efficiency': efficiency,
                'breakeven': put['strike'] - net_cost,
                'expiration': expiration_date,
                'days_to_exp': days_to_exp
            })
    
    return combinations

def rank_combinations(combinations):
    if not combinations:
        return []
    
    # Simple ranking based on efficiency and delta
    def score(combo):
        return combo['efficiency'] * 0.6 + (combo['net_delta'] / 10) * 0.4
    
    return sorted(combinations, key=score, reverse=True)

def format_analysis_result(combinations, ticker, strategy_type):
    if not combinations:
        return {
            "summary": f"No valid {strategy_type.lower()} strategies found for {ticker}.",
            "risk": "",
            "pricing_comparison": "",
            "top_5": []
        }
    
    best = combinations[0]
    cost_display = f"${abs(best['net_cost']):.2f} {'CREDIT' if best['net_cost'] < 0 else 'DEBIT'}"
    
    summary = f"""
🎯 TOP RECOMMENDED TRADE
Expiration: {best['expiration']} ({best['days_to_exp']} days)
"""
    
    if strategy_type == "Bullish":
        summary += f"""Strikes: Long Call: ${best['long_call_strike']:.2f}, Short Put: ${best['short_put_strike']:.2f}
Net Cost: {cost_display}
Breakeven: ${best['breakeven']:.2f}
Net Vega: {best['net_vega']:.3f}
Efficiency: {best['efficiency']:.1%}
"""
    else:
        summary += f"""Strikes: Long Put: ${best['long_put_strike']:.2f}, Short Call: ${best['short_call_strike']:.2f}
Net Cost: {cost_display}
Breakeven: ${best['breakeven']:.2f}
Net Vega: {best['net_vega']:.3f}
Efficiency: {best['efficiency']:.1%}
"""
    
    risk_warning = f"""
⚠️  STRATEGY OVERVIEW & RISK
A {strategy_type} Risk Reversal creates a synthetic {'long' if strategy_type == 'Bullish' else 'short'} stock position with low or zero cost. 
The primary risk is the short {'put' if strategy_type == 'Bullish' else 'call'}. Maximum loss is {'limited' if strategy_type == 'Bullish' else 'unlimited'}.
"""
    
    # Create top 5 table
    top_5 = []
    for i, combo in enumerate(combinations[:5]):
        if strategy_type == "Bullish":
            strikes = f"${combo['long_call_strike']:.2f}/{combo['short_put_strike']:.2f}"
        else:
            strikes = f"${combo['long_put_strike']:.2f}/{combo['short_call_strike']:.2f}"
        
        cost_txt = f"${abs(combo['net_cost']):.2f} {'CR' if combo['net_cost'] < 0 else 'DB'}"
        top_5.append([
            str(i+1),
            combo['expiration'],
            strikes,
            cost_txt,
            f"{combo['net_vega']:.3f}",
            f"{combo['efficiency']:.1%}",
            f"{combo['efficiency']:.3f}"
        ])
    
    return {
        "summary": summary.strip(),
        "risk": risk_warning.strip(),
        "pricing_comparison": "",
        "top_5": top_5
    }

def run_bullish_analysis(ticker: str, min_dte: int, max_dte: int) -> dict:
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        history_data = stock.history(period='1d')
        
        if history_data.empty:
            return format_analysis_result([], ticker, "Bullish")
        
        underlying_price = history_data['Close'].iloc[-1]
        time.sleep(0.4)
        
        today = datetime.now()
        
        # Get available options
        try:
            expirations = stock.options
            if not expirations:
                return format_analysis_result([], ticker, "Bullish")
        except Exception:
            return format_analysis_result([], ticker, "Bullish")

        valid_expirations = [exp for exp in expirations if min_dte <= (datetime.strptime(exp, "%Y-%m-%d") - today).days <= max_dte]
        time.sleep(0.4)
        
        if not valid_expirations:
            return format_analysis_result([], ticker, "Bullish")
        
        exp_to_analyze = valid_expirations[:3]
        all_combinations = []
        
        for expiration in exp_to_analyze:
            time.sleep(0.4)
            calls, puts = get_options_data(ticker, expiration, underlying_price)
            if not calls or not puts:
                continue
           
            combinations = analyze_bullish_risk_reversal(calls, puts, underlying_price, expiration)
            all_combinations.extend(combinations)
        
        if not all_combinations:
            return format_analysis_result([], ticker, "Bullish")
        
        ranked_results = rank_combinations(all_combinations)
        return format_analysis_result(ranked_results, ticker, "Bullish")
        
    except Exception as e:
        return {
            "summary": f"Analysis Error: {str(e)}",
            "risk": "",
            "pricing_comparison": "",
            "top_5": []
        }

def run_bearish_analysis(ticker: str, min_dte: int, max_dte: int) -> dict:
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        history_data = stock.history(period='1d')
        
        if history_data.empty:
            return format_analysis_result([], ticker, "Bearish")
        
        underlying_price = history_data['Close'].iloc[-1]
        time.sleep(0.4)
        
        today = datetime.now()
        
        # Get available options
        try:
            expirations = stock.options
            if not expirations:
                return format_analysis_result([], ticker, "Bearish")
        except Exception:
            return format_analysis_result([], ticker, "Bearish")

        valid_expirations = [exp for exp in expirations if min_dte <= (datetime.strptime(exp, "%Y-%m-%d") - today).days <= max_dte]
        time.sleep(0.4)
        
        if not valid_expirations:
            return format_analysis_result([], ticker, "Bearish")
        
        exp_to_analyze = valid_expirations[:3]
        all_combinations = []
        
        for expiration in exp_to_analyze:
            time.sleep(0.4)
            calls, puts = get_options_data(ticker, expiration, underlying_price)
            if not calls or not puts:
                continue
           
            combinations = analyze_bearish_risk_reversal(calls, puts, underlying_price, expiration)
            all_combinations.extend(combinations)
        
        if not all_combinations:
            return format_analysis_result([], ticker, "Bearish")
        
        ranked_results = rank_combinations(all_combinations)
        return format_analysis_result(ranked_results, ticker, "Bearish")
        
    except Exception as e:
        return {
            "summary": f"Analysis Error: {str(e)}",
            "risk": "",
            "pricing_comparison": "",
            "top_5": []
        }