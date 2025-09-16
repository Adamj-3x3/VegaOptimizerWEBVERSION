import yfinance as yf
import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta
import warnings
import logging
import time
import os

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

warnings.filterwarnings('ignore')


# -------------------------------
# Black-Scholes and Data Functions
# -------------------------------
def d1(S, K, T, r, sigma, q=0.0):
    if T <= 0 or sigma <= 0: return np.inf if S > K else -np.inf
    return (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))


def d2(S, K, T, r, sigma, q=0.0):
    return d1(S, K, T, r, sigma, q) - sigma * np.sqrt(T)


def bs_vega(S, K, T, r, sigma, q=0.0):
    if T <= 0 or sigma <= 0: return 0
    D1 = d1(S, K, T, r, sigma, q)
    return S * np.exp(-q * T) * norm.pdf(D1) * np.sqrt(T) / 100


def bs_delta(S, K, T, r, sigma, option_type='call', q=0.0):
    if T <= 0: return 1.0 if S > K and option_type == 'call' else (-1.0 if S < K and option_type == 'put' else 0.0)
    D1 = d1(S, K, T, r, sigma, q)
    return np.exp(-q * T) * norm.cdf(D1) if option_type == 'call' else np.exp(-q * T) * (norm.cdf(D1) - 1)


def get_options_data(ticker, expiration, underlying_price):
    try:
        stock = yf.Ticker(ticker)
        opt_chain = stock.option_chain(expiration)
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

    def process_df(input_df):
        if input_df is None or input_df.empty: return pd.DataFrame()
        df = input_df.copy()
        df.dropna(subset=['impliedVolatility', 'bid', 'ask'], inplace=True)
        if df.empty: return pd.DataFrame()
        mask = (((df['volume'] > 0) | (df['openInterest'] > 0)) & (df['impliedVolatility'] > 0.01) & (df['bid'] > 0) & (
                    (df['ask'] - df['bid']) / df['ask'] < 0.6))
        filtered_df = df[mask].copy()
        if not filtered_df.empty:
            filtered_df['moneyness'] = filtered_df['strike'] / underlying_price
            filtered_df['expiration'] = expiration
        return filtered_df

    calls = process_df(opt_chain.calls)
    puts = process_df(opt_chain.puts)

    # Add a small delay to be respectful to the API
    time.sleep(0.2)

    return calls, puts


# -------------------------------
# Smarter Strategy Engine
# -------------------------------
def analyze_bullish_risk_reversal(calls, puts, underlying_price, expiration_date, risk_free_rate=0.045,
                                  dividend_yield=0.0):
    today = pd.to_datetime(datetime.now().date())
    exp_date = pd.to_datetime(expiration_date)
    T = max((exp_date - today).days / 365.0, 1 / (365 * 24))
    days_to_exp = (exp_date - today).days

    for df, option_type in [(calls, 'call'), (puts, 'put')]:
        if df.empty: continue
        df['vega'] = df.apply(
            lambda row: bs_vega(underlying_price, row['strike'], T, risk_free_rate, row['impliedVolatility'],
                                dividend_yield), axis=1)
        df['delta'] = df.apply(
            lambda row: bs_delta(underlying_price, row['strike'], T, risk_free_rate, row['impliedVolatility'],
                                 option_type, dividend_yield), axis=1)

    otm_calls = calls[calls['strike'] > underlying_price].copy()
    otm_puts = puts[puts['strike'] < underlying_price].copy()

    max_strike_distance = underlying_price * 0.75
    otm_calls = otm_calls[otm_calls['strike'] < underlying_price + max_strike_distance]
    otm_puts = otm_puts[otm_puts['strike'] > underlying_price - max_strike_distance]

    if otm_calls.empty or otm_puts.empty:
        return []

    combinations = []
    for _, call in otm_calls.iterrows():
        for _, put in otm_puts.iterrows():
            if call['strike'] <= put['strike']: continue
            combo = create_bullish_strategy_combination(call, put)
            if combo and is_valid_bullish_combo(combo):
                combo.update({'strategy_type': 'Bullish Risk Reversal', 'expiration': expiration_date,
                              'days_to_exp': days_to_exp})
                combinations.append(combo)
    return combinations


def analyze_bearish_risk_reversal(calls, puts, underlying_price, expiration_date, risk_free_rate=0.045,
                                  dividend_yield=0.0):
    today = pd.to_datetime(datetime.now().date())
    exp_date = pd.to_datetime(expiration_date)
    T = max((exp_date - today).days / 365.0, 1 / (365 * 24))
    days_to_exp = (exp_date - today).days

    for df, option_type in [(calls, 'call'), (puts, 'put')]:
        if df.empty: continue
        df['vega'] = df.apply(
            lambda row: bs_vega(underlying_price, row['strike'], T, risk_free_rate, row['impliedVolatility'],
                                dividend_yield), axis=1)
        df['delta'] = df.apply(
            lambda row: bs_delta(underlying_price, row['strike'], T, risk_free_rate, row['impliedVolatility'],
                                 option_type, dividend_yield), axis=1)

    otm_calls = calls[calls['strike'] > underlying_price].copy()
    otm_puts = puts[puts['strike'] < underlying_price].copy()

    max_strike_distance = underlying_price * 0.75
    otm_calls = otm_calls[otm_calls['strike'] < underlying_price + max_strike_distance]
    otm_puts = otm_puts[otm_puts['strike'] > underlying_price - max_strike_distance]

    if otm_calls.empty or otm_puts.empty:
        return []

    combinations = []
    for _, put in otm_puts.iterrows():
        for _, call in otm_calls.iterrows():
            if put['strike'] >= call['strike']: continue
            combo = create_bearish_strategy_combination(put, call)
            if combo and is_valid_bearish_combo(combo):
                combo.update({'strategy_type': 'Bearish Risk Reversal', 'expiration': expiration_date,
                              'days_to_exp': days_to_exp})
                combinations.append(combo)
    return combinations


def create_bullish_strategy_combination(call_row, put_row):
    try:
        net_cost = call_row['ask'] - put_row['bid']
        strike_diff = call_row['strike'] - put_row['strike']
        efficiency = -net_cost / strike_diff if strike_diff > 0 else 0
        
        # Add detailed logging for debugging
        logging.info(f"Bullish Risk Reversal Calculation:")
        logging.info(f"  Long Call: Strike=${call_row['strike']:.2f}, Ask=${call_row['ask']:.2f}, Bid=${call_row['bid']:.2f}")
        logging.info(f"  Short Put: Strike=${put_row['strike']:.2f}, Ask=${put_row['ask']:.2f}, Bid=${put_row['bid']:.2f}")
        logging.info(f"  Net Cost: ${call_row['ask']:.2f} - ${put_row['bid']:.2f} = ${net_cost:.2f}")
        logging.info(f"  Mid-price calculation: ${(call_row['bid'] + call_row['ask'])/2:.2f} - ${(put_row['bid'] + put_row['ask'])/2:.2f} = ${((call_row['bid'] + call_row['ask'])/2) - ((put_row['bid'] + put_row['ask'])/2):.2f}")
        
        # Calculate alternative pricing methods for comparison
        pricing_comparison = calculate_alternative_pricing(call_row, put_row, 'bullish')
        
        return {
            'long_call_strike': call_row['strike'], 'short_put_strike': put_row['strike'],
            'net_cost': net_cost, 'iv_advantage': put_row['impliedVolatility'] - call_row['impliedVolatility'],
            'net_delta': call_row['delta'] - put_row['delta'], 'net_vega': call_row['vega'] - put_row['vega'],
            'max_loss_down': put_row['strike'] - (put_row['bid'] - call_row['ask']),
            'breakeven': call_row['strike'] + net_cost,
            'efficiency': efficiency,
            'pricing_comparison': pricing_comparison
        }
    except (KeyError, TypeError):
        return None


def create_bearish_strategy_combination(put_row, call_row):
    try:
        net_cost = put_row['ask'] - call_row['bid']
        strike_diff = call_row['strike'] - put_row['strike']
        efficiency = -net_cost / strike_diff if strike_diff > 0 else 0
        
        # Add detailed logging for debugging
        logging.info(f"Bearish Risk Reversal Calculation:")
        logging.info(f"  Long Put: Strike=${put_row['strike']:.2f}, Ask=${put_row['ask']:.2f}, Bid=${put_row['bid']:.2f}")
        logging.info(f"  Short Call: Strike=${call_row['strike']:.2f}, Ask=${call_row['ask']:.2f}, Bid=${call_row['bid']:.2f}")
        logging.info(f"  Net Cost: ${put_row['ask']:.2f} - ${call_row['bid']:.2f} = ${net_cost:.2f}")
        logging.info(f"  Mid-price calculation: ${(put_row['bid'] + put_row['ask'])/2:.2f} - ${(call_row['bid'] + call_row['ask'])/2:.2f} = ${((put_row['bid'] + put_row['ask'])/2) - ((call_row['bid'] + call_row['ask'])/2):.2f}")
        
        # Calculate alternative pricing methods for comparison
        pricing_comparison = calculate_alternative_pricing(call_row, put_row, 'bearish')
        
        return {
            'long_put_strike': put_row['strike'], 'short_call_strike': call_row['strike'],
            'net_cost': net_cost, 'iv_advantage': call_row['impliedVolatility'] - put_row['impliedVolatility'],
            'net_delta': put_row['delta'] - call_row['delta'], 'net_vega': put_row['vega'] - call_row['vega'],
            'max_loss_up': call_row['strike'] + (call_row['bid'] - put_row['ask']),
            'breakeven': put_row['strike'] - net_cost,
            'efficiency': efficiency,
            'pricing_comparison': pricing_comparison
        }
    except (KeyError, TypeError):
        return None


def is_valid_bullish_combo(combo):
    if not combo: return False
    if abs(combo['net_cost']) > 20: return False
    if combo['net_delta'] <= 0.1 or combo['net_vega'] <= 0: return False
    return True


def is_valid_bearish_combo(combo):
    if not combo: return False
    if abs(combo['net_cost']) > 20: return False
    if combo['net_delta'] >= -0.1 or combo['net_vega'] > 0.01: return False
    return True


def rank_combinations(combinations):
    if not combinations: return []
    df = pd.DataFrame(combinations)

    def safe_normalize(series, reverse=False):
        if series.std() == 0 or len(series) < 2: return pd.Series([0.5] * len(series), index=series.index)
        norm = (series - series.min()) / (series.max() - series.min())
        return 1 - norm if reverse else norm

    df['delta_score'] = safe_normalize(df['net_delta'])
    df['vega_score'] = safe_normalize(df['net_vega'])
    df['efficiency_score'] = safe_normalize(df['efficiency'])
    df['total_score'] = (df['delta_score'] * 0.40 + df['efficiency_score'] * 0.40 + df['vega_score'] * 0.20)
    return df.sort_values('total_score', ascending=False)


def rank_bearish_combinations(combinations):
    if not combinations: return []
    df = pd.DataFrame(combinations)

    def safe_normalize(series, reverse=False):
        if series.std() == 0 or len(series) < 2: return pd.Series([0.5] * len(series), index=series.index)
        norm = (series - series.min()) / (series.max() - series.min())
        return 1 - norm if reverse else norm

    # For bearish, we want negative delta (more negative is better), low absolute vega, and good efficiency
    df['delta_score'] = safe_normalize(df['net_delta'], reverse=True)  # More negative delta is better
    df['vega_score'] = safe_normalize(df['net_vega'].abs(), reverse=True)  # Lower absolute vega is better
    df['efficiency_score'] = safe_normalize(df['efficiency'])
    df['total_score'] = (df['delta_score'] * 0.40 + df['efficiency_score'] * 0.40 + df['vega_score'] * 0.20)
    return df.sort_values('total_score', ascending=False)


# -------------------------------
# Text Report Formatting
# -------------------------------
def format_text_report(results, analysis_summary, ticker, strategy_type):
    """Format analysis results into a clean, readable text report."""
    if results is None or results.empty:
        return f"No valid {strategy_type.lower()} strategies found for {ticker}."
    
    best = results.iloc[0]
    cost_display = f"${abs(best['net_cost']):.2f} {'CREDIT' if best['net_cost'] < 0 else 'DEBIT'}"
    
    # Add pricing comparison section for debugging
    pricing_comparison = ""
    if 'pricing_comparison' in best:
        pc = best['pricing_comparison']
        pricing_comparison = f"""
🔍 PRICING COMPARISON (for debugging Robinhood discrepancy)
Current Method (Worst-case): ${pc['current_method']:.2f} {'CREDIT' if pc['current_method'] < 0 else 'DEBIT'}
Mid-Price Method (Robinhood likely): ${pc['mid_price_method']:.2f} {'CREDIT' if pc['mid_price_method'] < 0 else 'DEBIT'}
Optimistic Method (Best-case): ${pc['optimistic_method']:.2f} {'CREDIT' if pc['optimistic_method'] < 0 else 'DEBIT'}
Bid-Ask Spreads: Call=${pc['call_spread']:.2f}, Put=${pc['put_spread']:.2f}, Total=${pc['total_spread']:.2f}
"""
    
    # Create summary section
    summary_lines = []
    for exp, count in analysis_summary.items():
        summary_lines.append(f"  {exp}: Found {count} valid trades")
    
    # Create top recommendations table
    table_lines = []
    table_lines.append("RANK | EXPIRATION | STRIKES | NET COST | NET VEGA | EFFICIENCY | SCORE")
    table_lines.append("-" * 80)
    
    for i, row in results.head(5).iterrows():
        if strategy_type == "Bullish":
            strikes = f"${row['long_call_strike']:.2f}/{row['short_put_strike']:.2f}"
        else:
            strikes = f"${row['long_put_strike']:.2f}/{row['short_call_strike']:.2f}"
        
        cost_txt = f"${abs(row['net_cost']):.2f} {'CR' if row['net_cost'] < 0 else 'DB'}"
        table_lines.append(f"{i+1:4} | {row['expiration']:10} | {strikes:15} | {cost_txt:9} | {row['net_vega']:8.3f} | {row['efficiency']:9.1%} | {row['total_score']:.3f}")
    
    # Create risk warning
    if strategy_type == "Bullish":
        risk_warning = f"""
⚠️  STRATEGY OVERVIEW & RISK
A Bullish Risk Reversal (Long OTM Call, Short OTM Put) creates a synthetic long stock position with low or zero cost. 
The primary risk is the short put. If the stock price falls below ${best['short_put_strike']:.2f}, you may be assigned 
100 shares per contract at that price. Maximum loss is up to ${best['max_loss_down']:.2f} per share if the stock goes to zero.
"""
    else:
        risk_warning = f"""
⚠️  STRATEGY OVERVIEW & RISK
A Bearish Risk Reversal (Long OTM Put, Short OTM Call) creates a synthetic short stock position with low or zero cost. 
The primary risk is the short call. If the stock price rises above ${best['short_call_strike']:.2f}, you may be assigned 
100 shares per contract at that price. Maximum loss is unlimited if the stock continues to rise.
"""
    
    # Assemble the complete report
    report = f"""
{'='*80}
🐂 {ticker} {strategy_type} Risk Reversal Report
{'='*80}

🎯 TOP RECOMMENDED TRADE
Expiration: {best['expiration']} ({best['days_to_exp']} days)
"""
    
    if strategy_type == "Bullish":
        report += f"""Strikes: Long Call: ${best['long_call_strike']:.2f}, Short Put: ${best['short_put_strike']:.2f}
Net Cost: {cost_display}
Breakeven: ${best['breakeven']:.2f}
Net Vega: {best['net_vega']:.3f}
Efficiency: {best['efficiency']:.1%}
"""
    else:
        report += f"""Strikes: Long Put: ${best['long_put_strike']:.2f}, Short Call: ${best['short_call_strike']:.2f}
Net Cost: {cost_display}
Breakeven: ${best['breakeven']:.2f}
Net Vega: {best['net_vega']:.3f}
Efficiency: {best['efficiency']:.1%}
"""
    
    report += f"""
{risk_warning}

🔎 ANALYSIS SUMMARY
"""
    for line in summary_lines:
        report += line + "\n"
    
    report += f"""
📊 TOP {min(len(results), 5)} COMBINATIONS (Max 3 Per Expiration)
"""
    for line in table_lines:
        report += line + "\n"
    
    # Add pricing comparison if available
    if pricing_comparison:
        report += pricing_comparison
    
    report += f"""
{'='*80}
Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}
"""
    
    return report


# -------------------------------
# Main Analysis Functions
# -------------------------------
def run_bullish_analysis(ticker: str, min_dte: int, max_dte: int) -> str:
    """
    Analyzes bullish strategies and returns a formatted text report.
    """
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        history_data = stock.history(period='1d')
        
        if history_data.empty:
            return f"Unable to fetch price data for {ticker}. Please check the ticker symbol and try again."
        
        underlying_price = history_data['Close'].iloc[-1]
        time.sleep(0.4)  # Gentle delay
        
        today = datetime.now()
        
        # Check for available options
        try:
            expirations = stock.options
            if not expirations:
                return f"No options data available for {ticker}. The ticker may not have an options market."
        except Exception:
             return f"Could not fetch option expiration dates for {ticker}."

        valid_expirations = [exp for exp in expirations if min_dte <= (datetime.strptime(exp, "%Y-%m-%d") - today).days <= max_dte]
        time.sleep(0.4)  # Gentle delay
        
        if not valid_expirations:
            return f"No expirations found in the specified date range for {ticker}."
        
        exp_to_analyze = valid_expirations[:3]
        analysis_summary = {}
        all_combinations = []
        
        for expiration in exp_to_analyze:
            print(f"\n⚡ Analyzing expiration: {expiration}...")
            time.sleep(0.4)  # Gentle delay
            calls, puts = get_options_data(ticker, expiration, underlying_price)
            if calls.empty or puts.empty:
                print(f"    - No suitable OTM options data found after cleaning.")
                analysis_summary[expiration] = 0
                continue
           
            combinations = analyze_bullish_risk_reversal(calls, puts, underlying_price, expiration)
            analysis_summary[expiration] = len(combinations)
            if combinations:
                print(f"    ✅ Found {len(combinations)} potential combinations.")
                all_combinations.extend(combinations)
            else:
                print(f"    - No valid combinations met the strategy criteria.")
        
        if not all_combinations:
            return f"No valid bullish strategies found for {ticker}."
        
        ranked_results = rank_combinations(all_combinations)
        if isinstance(ranked_results, list) and len(ranked_results) == 0:
            return f"No valid bullish strategies found for {ticker}."
        
        # Ensure ranked_results is a DataFrame
        if not isinstance(ranked_results, pd.DataFrame):
            return f"No valid bullish strategies found for {ticker}."
        
        final_results = ranked_results.groupby('expiration').head(3).sort_values('total_score', ascending=False).reset_index(drop=True)
        
        if final_results.empty:
            return f"No valid bullish strategies remained after filtering for {ticker}."
        
        return format_text_report(final_results, analysis_summary, ticker, "Bullish")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"An unexpected error occurred while analyzing {ticker}.\nError: {e}"


def run_bearish_analysis(ticker: str, min_dte: int, max_dte: int) -> str:
    """
    Analyzes bearish strategies and returns a formatted text report.
    """
    try:
        # Get stock data
        stock = yf.Ticker(ticker)
        history_data = stock.history(period='1d')
        
        if history_data.empty:
            return f"Unable to fetch price data for {ticker}. Please check the ticker symbol and try again."
        
        underlying_price = history_data['Close'].iloc[-1]
        time.sleep(0.4)  # Gentle delay
        
        today = datetime.now()
        
        # Check for available options
        try:
            expirations = stock.options
            if not expirations:
                return f"No options data available for {ticker}. The ticker may not have an options market."
        except Exception:
             return f"Could not fetch option expiration dates for {ticker}."

        valid_expirations = [exp for exp in expirations if min_dte <= (datetime.strptime(exp, "%Y-%m-%d") - today).days <= max_dte]
        time.sleep(0.4)  # Gentle delay
        
        if not valid_expirations:
            return f"No expirations found in the specified date range for {ticker}."
        
        exp_to_analyze = valid_expirations[:3]
        analysis_summary = {}
        all_combinations = []
        
        for expiration in exp_to_analyze:
            print(f"\n⚡ Analyzing expiration: {expiration}...")
            time.sleep(0.4)  # Gentle delay
            calls, puts = get_options_data(ticker, expiration, underlying_price)
            if calls.empty or puts.empty:
                print(f"    - No suitable OTM options data found after cleaning.")
                analysis_summary[expiration] = 0
                continue
           
            combinations = analyze_bearish_risk_reversal(calls, puts, underlying_price, expiration)
            analysis_summary[expiration] = len(combinations)
            if combinations:
                print(f"    ✅ Found {len(combinations)} potential combinations.")
                all_combinations.extend(combinations)
            else:
                print(f"    - No valid combinations met the strategy criteria.")
        
        if not all_combinations:
            return f"No valid bearish strategies found for {ticker}."
        
        ranked_results = rank_bearish_combinations(all_combinations)
        if isinstance(ranked_results, list) and len(ranked_results) == 0:
            return f"No valid bearish strategies found for {ticker}."
        
        # Ensure ranked_results is a DataFrame
        if not isinstance(ranked_results, pd.DataFrame):
            return f"No valid bearish strategies found for {ticker}."
        
        final_results = ranked_results.groupby('expiration').head(3).sort_values('total_score', ascending=False).reset_index(drop=True)
        
        if final_results.empty:
            return f"No valid bearish strategies remained after filtering for {ticker}."
        
        return format_text_report(final_results, analysis_summary, ticker, "Bearish")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"An unexpected error occurred while analyzing {ticker}.\nError: {e}"


# -------------------------------
# Alternative Pricing Methods for Comparison
# -------------------------------
def calculate_alternative_pricing(call_row, put_row, strategy_type='bullish'):
    """
    Calculate net cost using different pricing methods for comparison with Robinhood.
    Returns a dictionary with various pricing scenarios.
    """
    try:
        # Current method (worst-case scenario)
        if strategy_type == 'bullish':
            current_net_cost = call_row['ask'] - put_row['bid']
        else:  # bearish
            current_net_cost = put_row['ask'] - call_row['bid']
        
        # Mid-price method (likely what Robinhood uses)
        call_mid = (call_row['bid'] + call_row['ask']) / 2
        put_mid = (put_row['bid'] + put_row['ask']) / 2
        
        if strategy_type == 'bullish':
            mid_net_cost = call_mid - put_mid
        else:  # bearish
            mid_net_cost = put_mid - call_mid
        
        # Optimistic method (best-case scenario)
        if strategy_type == 'bullish':
            optimistic_net_cost = call_row['bid'] - put_row['ask']
        else:  # bearish
            optimistic_net_cost = put_row['bid'] - call_row['ask']
        
        # Bid-ask spreads
        call_spread = call_row['ask'] - call_row['bid']
        put_spread = put_row['ask'] - put_row['bid']
        
        return {
            'current_method': current_net_cost,
            'mid_price_method': mid_net_cost,
            'optimistic_method': optimistic_net_cost,
            'call_spread': call_spread,
            'put_spread': put_spread,
            'total_spread': call_spread + put_spread,
            'call_mid': call_mid,
            'put_mid': put_mid
        }
    except (KeyError, TypeError):
        return None
