import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from scipy.stats import norm
import yfinance as yf
from datetime import datetime
import threading
import time

class BinomialModel:
    def __init__(self, S, K, r, sigma, T, q, steps=100):
        self.S = S
        self.K = K
        self.r = r
        self.sigma = sigma
        self.T = T
        self.q = q
        self.steps = steps
        
        # Calculate binomial parameters
        self.dt = T / steps
        self.u = np.exp(sigma * np.sqrt(self.dt))
        self.d = 1 / self.u
        self.p = (np.exp((r - q) * self.dt) - self.d) / (self.u - self.d)
        self.discount = np.exp(-r * self.dt)
    
    def price_american_option(self, option_type='Call'):
        # Initialize asset price tree
        asset_prices = np.zeros((self.steps + 1, self.steps + 1))
        for i in range(self.steps + 1):
            for j in range(i + 1):
                asset_prices[j, i] = self.S * (self.u ** j) * (self.d ** (i - j))
        
        # Initialize option value tree
        option_values = np.zeros((self.steps + 1, self.steps + 1))
        
        # Calculate option values at expiration
        for j in range(self.steps + 1):
            if option_type == 'Call':
                option_values[j, self.steps] = max(0, asset_prices[j, self.steps] - self.K)
            else:
                option_values[j, self.steps] = max(0, self.K - asset_prices[j, self.steps])
        
        # Work backwards through the tree
        early_exercise_nodes = []
        for i in range(self.steps - 1, -1, -1):
            for j in range(i + 1):
                # Calculate continuation value
                continuation_value = self.discount * (
                    self.p * option_values[j + 1, i + 1] + 
                    (1 - self.p) * option_values[j, i + 1]
                )
                
                # Calculate exercise value
                if option_type == 'Call':
                    exercise_value = max(0, asset_prices[j, i] - self.K)
                else:
                    exercise_value = max(0, self.K - asset_prices[j, i])
                
                # American option: take maximum
                option_values[j, i] = max(continuation_value, exercise_value)
                
                # Track early exercise
                if exercise_value > continuation_value and exercise_value > 0:
                    early_exercise_nodes.append({
                        'time_step': i,
                        'stock_price': asset_prices[j, i],
                        'exercise_value': exercise_value,
                        'continuation_value': continuation_value
                    })
        
        # Calculate European price for comparison
        european_price = self._price_european_option(option_type)
        american_price = option_values[0, 0]
        
        return {
            'american_price': american_price,
            'european_price': european_price,
            'early_exercise_premium': american_price - european_price,
            'early_exercise_nodes': early_exercise_nodes,
            'should_exercise_now': self._should_exercise_now(option_type)
        }
    
    def _price_european_option(self, option_type='Call'):
        # Simple European binomial pricing
        option_values = np.zeros((self.steps + 1, self.steps + 1))
        
        # Asset prices
        for i in range(self.steps + 1):
            for j in range(i + 1):
                S_price = self.S * (self.u ** j) * (self.d ** (i - j))
                if i == self.steps:
                    if option_type == 'Call':
                        option_values[j, i] = max(0, S_price - self.K)
                    else:
                        option_values[j, i] = max(0, self.K - S_price)
        
        # Work backwards
        for i in range(self.steps - 1, -1, -1):
            for j in range(i + 1):
                option_values[j, i] = self.discount * (
                    self.p * option_values[j + 1, i + 1] + 
                    (1 - self.p) * option_values[j, i + 1]
                )
        
        return option_values[0, 0]
    
    def _should_exercise_now(self, option_type='Call'):
        if option_type == 'Call':
            intrinsic_value = max(0, self.S - self.K)
        else:
            intrinsic_value = max(0, self.K - self.S)
        
        if intrinsic_value <= 0:
            return {
                'should_exercise': False,
                'reason': 'Option is out of the money',
                'intrinsic_value': intrinsic_value
            }
        
        # Simple heuristic for early exercise
        should_exercise = False
        reasons = []
        
        if option_type == 'Put':
            if self.S < self.K * 0.8:
                should_exercise = True
                reasons.append("Deep in-the-money put")
            if self.r > 0.05 and self.S < self.K * 0.9:
                should_exercise = True
                reasons.append("High interest rates favor early exercise")
        
        if option_type == 'Call' and self.q > self.r:
            should_exercise = True
            reasons.append("High dividend yield - consider exercising before ex-dividend")
        
        return {
            'should_exercise': should_exercise,
            'intrinsic_value': intrinsic_value,
            'reasons': reasons
        }

class OptionPricingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Option Pricing with American Options & Early Exercise Analysis")
        self.root.geometry("1600x1000")
        
        # Parameters
        self.params = {
            'S': tk.DoubleVar(value=100.0),
            'K': tk.DoubleVar(value=100.0),
            'r': tk.DoubleVar(value=0.05),
            'sigma': tk.DoubleVar(value=0.20),
            'T': tk.DoubleVar(value=0.25),
            'q': tk.DoubleVar(value=0.02)
        }
        
        self.option_type = tk.StringVar(value="Call")
        self.binomial_steps = tk.IntVar(value=100)
        
        self.create_interface()
        self.update_calculations()
    
    def black_scholes_price(self, S, K, r, sigma, T, q, option_type='Call'):
        try:
            if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
                return 0.0
            
            d1 = (np.log(S/K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            if option_type == 'Call':
                price = S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
            else:
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)
            
            return max(price, 0.0)
        except:
            return 0.0
    
    def calculate_greeks(self, S, K, r, sigma, T, q, option_type='Call'):
        try:
            if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
                return {'Delta': 0, 'Gamma': 0, 'Theta': 0, 'Vega': 0, 'Rho': 0}
            
            d1 = (np.log(S/K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            pdf_d1 = norm.pdf(d1)
            cdf_d1 = norm.cdf(d1)
            cdf_d2 = norm.cdf(d2)
            
            if option_type == 'Call':
                delta = np.exp(-q * T) * cdf_d1
                rho = K * T * np.exp(-r * T) * cdf_d2 / 100
            else:
                delta = -np.exp(-q * T) * norm.cdf(-d1)
                rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
            
            gamma = (pdf_d1 * np.exp(-q * T)) / (S * sigma * np.sqrt(T))
            theta = -((S * pdf_d1 * sigma * np.exp(-q * T)) / (2 * np.sqrt(T)) + 
                     r * K * np.exp(-r * T) * (cdf_d2 if option_type == 'Call' else norm.cdf(-d2))) / 365
            vega = S * np.exp(-q * T) * pdf_d1 * np.sqrt(T) / 100
            
            return {
                'Delta': delta,
                'Gamma': gamma,
                'Theta': theta,
                'Vega': vega,
                'Rho': rho
            }
        except:
            return {'Delta': 0, 'Gamma': 0, 'Theta': 0, 'Vega': 0, 'Rho': 0}
    
    def create_interface(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # Left panel - Controls
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Right panel - Results and Charts
        result_frame = ttk.Frame(main_frame)
        result_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(1, weight=1)
        
        self.create_controls(control_frame)
        self.create_results(result_frame)
        self.create_charts(result_frame)
    
    def create_controls(self, parent):
        # Live Data Section
        data_frame = ttk.LabelFrame(parent, text="Live Data", padding="10")
        data_frame.pack(fill=tk.X, pady=(0, 10))
        
        symbol_frame = ttk.Frame(data_frame)
        symbol_frame.pack(fill=tk.X)
        
        ttk.Label(symbol_frame, text="Symbol:").pack(side=tk.LEFT)
        self.symbol_entry = ttk.Entry(symbol_frame, width=8)
        self.symbol_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.symbol_entry.insert(0, "AAPL")
        
        ttk.Button(symbol_frame, text="Fetch Data", command=self.fetch_data).pack(side=tk.LEFT)
        
        self.data_status = ttk.Label(data_frame, text="Ready", foreground="green")
        self.data_status.pack(anchor=tk.W, pady=(5, 0))
        
        # Option Settings
        option_frame = ttk.LabelFrame(parent, text="Option Settings", padding="10")
        option_frame.pack(fill=tk.X, pady=(0, 10))
        
        type_frame = ttk.Frame(option_frame)
        type_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(type_frame, text="Type:").pack(side=tk.LEFT)
        ttk.Radiobutton(type_frame, text="Call", variable=self.option_type, value="Call", 
                       command=self.update_calculations).pack(side=tk.LEFT, padx=(10, 10))
        ttk.Radiobutton(type_frame, text="Put", variable=self.option_type, value="Put", 
                       command=self.update_calculations).pack(side=tk.LEFT)
        
        steps_frame = ttk.Frame(option_frame)
        steps_frame.pack(fill=tk.X)
        
        ttk.Label(steps_frame, text="Binomial Steps:").pack(side=tk.LEFT)
        self.steps_label = ttk.Label(steps_frame, text="100")
        self.steps_label.pack(side=tk.RIGHT)
        
        steps_scale = ttk.Scale(steps_frame, from_=10, to=300, variable=self.binomial_steps, 
                               orient=tk.HORIZONTAL, command=self.on_steps_change)
        steps_scale.pack(fill=tk.X, pady=(5, 0))
        
        # Parameters
        params_frame = ttk.LabelFrame(parent, text="Parameters", padding="10")
        params_frame.pack(fill=tk.X)
        
        param_configs = {
            'S': {'label': 'Stock Price ($)', 'min': 1, 'max': 500},
            'K': {'label': 'Strike Price ($)', 'min': 1, 'max': 500},
            'r': {'label': 'Risk-free Rate', 'min': 0, 'max': 0.20},
            'sigma': {'label': 'Volatility', 'min': 0.01, 'max': 2.0},
            'T': {'label': 'Time to Expiration (years)', 'min': 0.01, 'max': 5},
            'q': {'label': 'Dividend Yield', 'min': 0, 'max': 0.20}
        }
        
        self.param_labels = {}
        
        for param, config in param_configs.items():
            frame = ttk.Frame(params_frame)
            frame.pack(fill=tk.X, pady=2)
            
            label_frame = ttk.Frame(frame)
            label_frame.pack(fill=tk.X)
            
            ttk.Label(label_frame, text=config['label']).pack(side=tk.LEFT)
            self.param_labels[param] = ttk.Label(label_frame, text=f"{self.params[param].get():.4f}")
            self.param_labels[param].pack(side=tk.RIGHT)
            
            scale = ttk.Scale(frame, from_=config['min'], to=config['max'], 
                             variable=self.params[param], orient=tk.HORIZONTAL,
                             command=lambda val, p=param: self.on_param_change(p))
            scale.pack(fill=tk.X)
        
        ttk.Button(params_frame, text="Reset", command=self.reset_parameters).pack(pady=(10, 0))
    
    def create_results(self, parent):
        results_frame = ttk.LabelFrame(parent, text="Results", padding="10")
        results_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        notebook = ttk.Notebook(results_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Pricing Tab
        pricing_frame = ttk.Frame(notebook, padding="10")
        notebook.add(pricing_frame, text="Pricing")
        
        # Black-Scholes
        bs_frame = ttk.LabelFrame(pricing_frame, text="Black-Scholes (European)", padding="5")
        bs_frame.pack(fill=tk.X, pady=(0, 5))
        
        bs_price_frame = ttk.Frame(bs_frame)
        bs_price_frame.pack(fill=tk.X)
        
        ttk.Label(bs_price_frame, text="Price:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.bs_price_label = ttk.Label(bs_price_frame, text="$0.00", font=('Arial', 10, 'bold'), 
                                       foreground='darkgreen')
        self.bs_price_label.pack(side=tk.RIGHT)
        
        # Binomial
        bin_frame = ttk.LabelFrame(pricing_frame, text="Binomial Model", padding="5")
        bin_frame.pack(fill=tk.X)
        
        euro_frame = ttk.Frame(bin_frame)
        euro_frame.pack(fill=tk.X)
        ttk.Label(euro_frame, text="European:").pack(side=tk.LEFT)
        self.euro_price_label = ttk.Label(euro_frame, text="$0.00")
        self.euro_price_label.pack(side=tk.RIGHT)
        
        amer_frame = ttk.Frame(bin_frame)
        amer_frame.pack(fill=tk.X)
        ttk.Label(amer_frame, text="American:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        self.amer_price_label = ttk.Label(amer_frame, text="$0.00", font=('Arial', 9, 'bold'), 
                                         foreground='darkblue')
        self.amer_price_label.pack(side=tk.RIGHT)
        
        prem_frame = ttk.Frame(bin_frame)
        prem_frame.pack(fill=tk.X)
        ttk.Label(prem_frame, text="Early Exercise Premium:").pack(side=tk.LEFT)
        self.premium_label = ttk.Label(prem_frame, text="$0.00", foreground='darkorange')
        self.premium_label.pack(side=tk.RIGHT)
        
        # Greeks Tab
        greeks_frame = ttk.Frame(notebook, padding="10")
        notebook.add(greeks_frame, text="Greeks")
        
        self.greeks_labels = {}
        greeks_info = ['Delta', 'Gamma', 'Theta', 'Vega', 'Rho']
        
        for greek in greeks_info:
            frame = ttk.Frame(greeks_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=f"{greek}:", width=8).pack(side=tk.LEFT)
            self.greeks_labels[greek] = ttk.Label(frame, text="0.000")
            self.greeks_labels[greek].pack(side=tk.LEFT)
        
        # Early Exercise Tab
        exercise_frame = ttk.Frame(notebook, padding="10")
        notebook.add(exercise_frame, text="Early Exercise")
        
        decision_frame = ttk.LabelFrame(exercise_frame, text="Exercise Decision", padding="10")
        decision_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.exercise_decision = ttk.Label(decision_frame, text="Analysis will appear here...", 
                                          font=('Arial', 10), wraplength=300)
        self.exercise_decision.pack()
        
        analysis_frame = ttk.LabelFrame(exercise_frame, text="Analysis", padding="10")
        analysis_frame.pack(fill=tk.BOTH, expand=True)
        
        self.exercise_text = tk.Text(analysis_frame, height=8, wrap=tk.WORD, font=('Arial', 9))
        scrollbar = ttk.Scrollbar(analysis_frame, orient=tk.VERTICAL, command=self.exercise_text.yview)
        self.exercise_text.configure(yscrollcommand=scrollbar.set)
        
        self.exercise_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_charts(self, parent):
        chart_frame = ttk.LabelFrame(parent, text="Analysis Charts", padding="5")
        chart_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.fig = Figure(figsize=(16, 10), dpi=80)
        self.fig.patch.set_facecolor('white')
        
        # Create 6 subplots (3x2)
        self.ax1 = self.fig.add_subplot(2, 3, 1)  # Price vs Stock Price
        self.ax2 = self.fig.add_subplot(2, 3, 2)  # Price vs Volatility
        self.ax3 = self.fig.add_subplot(2, 3, 3)  # Price vs Time
        self.ax4 = self.fig.add_subplot(2, 3, 4)  # Early Exercise Premium
        self.ax5 = self.fig.add_subplot(2, 3, 5)  # Greeks
        self.ax6 = self.fig.add_subplot(2, 3, 6)  # Option Values
        
        self.fig.subplots_adjust(left=0.08, right=0.95, top=0.95, bottom=0.08, 
                                hspace=0.3, wspace=0.3)
        
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def fetch_data(self):
        def fetch():
            try:
                symbol = self.symbol_entry.get().upper().strip()
                if not symbol:
                    return
                
                self.root.after(0, lambda: self.data_status.config(text="Fetching...", foreground="orange"))
                
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                
                if hist.empty:
                    self.root.after(0, lambda: self.data_status.config(text="No data found", foreground="red"))
                    return
                
                current_price = float(hist['Close'].iloc[-1])
                
                # Calculate volatility
                returns = hist['Close'].pct_change().dropna()
                if len(returns) > 1:
                    volatility = float(returns.std() * np.sqrt(252))
                else:
                    volatility = 0.2
                
                def update_gui():
                    self.params['S'].set(current_price)
                    if volatility > 0:
                        self.params['sigma'].set(min(volatility, 2.0))
                    
                    for param in self.params:
                        self.param_labels[param].config(text=f"{self.params[param].get():.4f}")
                    
                    self.data_status.config(text=f"Updated: {symbol} - ${current_price:.2f}", foreground="green")
                    self.update_calculations()
                
                self.root.after(0, update_gui)
                
            except Exception as e:
                self.root.after(0, lambda: self.data_status.config(text=f"Error: {str(e)[:30]}", foreground="red"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def on_param_change(self, param):
        self.param_labels[param].config(text=f"{self.params[param].get():.4f}")
        self.update_calculations()
    
    def on_steps_change(self, value):
        steps = int(float(value))
        self.binomial_steps.set(steps)
        self.steps_label.config(text=str(steps))
        self.update_calculations()
    
    def update_calculations(self):
        try:
            # Get parameters
            S = self.params['S'].get()
            K = self.params['K'].get()
            r = self.params['r'].get()
            sigma = self.params['sigma'].get()
            T = self.params['T'].get()
            q = self.params['q'].get()
            option_type = self.option_type.get()
            steps = self.binomial_steps.get()
            
            # Black-Scholes
            bs_price = self.black_scholes_price(S, K, r, sigma, T, q, option_type)
            self.bs_price_label.config(text=f"${bs_price:.4f}")
            
            # Greeks
            greeks = self.calculate_greeks(S, K, r, sigma, T, q, option_type)
            for greek, value in greeks.items():
                self.greeks_labels[greek].config(text=f"{value:.4f}")
            
            # Binomial
            model = BinomialModel(S, K, r, sigma, T, q, steps)
            result = model.price_american_option(option_type)
            
            self.euro_price_label.config(text=f"${result['european_price']:.4f}")
            self.amer_price_label.config(text=f"${result['american_price']:.4f}")
            self.premium_label.config(text=f"${result['early_exercise_premium']:.4f}")
            
            # Early exercise analysis
            self.update_exercise_analysis(result)
            
            # Update charts
            self.update_charts()
            
        except Exception as e:
            print(f"Error in calculations: {e}")
    
    def update_exercise_analysis(self, result):
        exercise_info = result['should_exercise_now']
        
        if exercise_info['should_exercise']:
            decision_text = "🔴 EXERCISE NOW - Early exercise recommended"
            decision_color = "red"
        else:
            decision_text = "🟢 HOLD - Continue holding the option"
            decision_color = "green"
        
        self.exercise_decision.config(text=decision_text, foreground=decision_color)
        
        # Analysis text
        self.exercise_text.delete(1.0, tk.END)
        
        analysis = f"""EARLY EXERCISE ANALYSIS
{'='*40}

Decision: {'EXERCISE' if exercise_info['should_exercise'] else 'HOLD'}

Intrinsic Value: ${exercise_info['intrinsic_value']:.4f}
Early Exercise Premium: ${result['early_exercise_premium']:.4f}

American Price: ${result['american_price']:.4f}
European Price: ${result['european_price']:.4f}

"""
        
        if exercise_info.get('reasons'):
            analysis += "Reasons for Early Exercise:\n"
            for reason in exercise_info['reasons']:
                analysis += f"• {reason}\n"
            analysis += "\n"
        
        analysis += """GENERAL GUIDANCE:
• American calls: Early exercise rare except before dividends
• American puts: More likely when deep in-the-money
• Consider transaction costs in real trading
• This is for educational purposes only
"""
        
        self.exercise_text.insert(1.0, analysis)
    
    def update_charts(self):
        try:
            S = self.params['S'].get()
            K = self.params['K'].get()
            r = self.params['r'].get()
            sigma = self.params['sigma'].get()
            T = self.params['T'].get()
            q = self.params['q'].get()
            option_type = self.option_type.get()
            steps = min(self.binomial_steps.get(), 100)  # Limit for performance
            
            # Clear all axes
            for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
                ax.clear()
            
            # Chart 1: Price vs Stock Price
            S_range = np.linspace(max(1, S * 0.7), S * 1.3, 20)
            bs_prices = [self.black_scholes_price(s, K, r, sigma, T, q, option_type) for s in S_range]
            
            american_prices = []
            european_prices = []
            for s in S_range:
                model = BinomialModel(s, K, r, sigma, T, q, steps)
                result = model.price_american_option(option_type)
                american_prices.append(result['american_price'])
                european_prices.append(result['european_price'])
            
            self.ax1.plot(S_range, bs_prices, 'b-', label='Black-Scholes', linewidth=2)
            self.ax1.plot(S_range, european_prices, 'g--', label='European', linewidth=2)
            self.ax1.plot(S_range, american_prices, 'r-', label='American', linewidth=2)
            self.ax1.axvline(S, color='gray', linestyle=':', alpha=0.7)
            self.ax1.set_title('Price vs Stock Price')
            self.ax1.set_xlabel('Stock Price ($)')
            self.ax1.set_ylabel('Option Price ($)')
            self.ax1.legend()
            self.ax1.grid(True, alpha=0.3)
            
            # Chart 2: Price vs Volatility
            vol_range = np.linspace(0.1, min(1.0, sigma * 2), 15)
            bs_vol_prices = [self.black_scholes_price(S, K, r, vol, T, q, option_type) for vol in vol_range]
            
            am_vol_prices = []
            eu_vol_prices = []
            for vol in vol_range:
                model = BinomialModel(S, K, r, vol, T, q, steps)
                result = model.price_american_option(option_type)
                am_vol_prices.append(result['american_price'])
                eu_vol_prices.append(result['european_price'])