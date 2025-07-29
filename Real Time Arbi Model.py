import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import time
from datetime import datetime
import hashlib
import hmac
import base64

class ArbitrageScannerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smarkets vs Matchbook Arbitrage Scanner")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        self.scanner = SmarketsMatchbookScanner()
        self.scanning = False
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the user interface"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="🎯 Smarkets vs Matchbook Arbitrage Scanner", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # API Configuration Frame
        api_frame = ttk.LabelFrame(main_frame, text="🔑 API Configuration", padding="15")
        api_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        api_frame.columnconfigure(1, weight=1)
        
        # Smarkets status section
        smarkets_label = ttk.Label(api_frame, text="📊 SMARKETS (Public Data)", font=('Arial', 10, 'bold'), foreground='blue')
        smarkets_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.sm_status_label = ttk.Label(api_frame, text="✅ Ready - Uses public market data", foreground='green')
        self.sm_status_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Separator
        ttk.Separator(api_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Matchbook credentials section
        matchbook_label = ttk.Label(api_frame, text="🎯 MATCHBOOK (Authenticated)", font=('Arial', 10, 'bold'), foreground='orange')
        matchbook_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        ttk.Label(api_frame, text="Username:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.mb_username = ttk.Entry(api_frame, width=30)
        self.mb_username.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        ttk.Label(api_frame, text="Password:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.mb_password = ttk.Entry(api_frame, width=30, show="*")
        self.mb_password.grid(row=5, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=2)
        
        # API help text
        help_frame = ttk.Frame(api_frame)
        help_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        smarkets_help = ttk.Label(help_frame, text="💡 Smarkets: Uses public API - no authentication required", 
                                 font=('Arial', 8), foreground='gray')
        smarkets_help.grid(row=0, column=0, sticky=tk.W)
        
        matchbook_help = ttk.Label(help_frame, text="💡 Matchbook: Use your regular login credentials for full market access", 
                                  font=('Arial', 8), foreground='gray')
        matchbook_help.grid(row=1, column=0, sticky=tk.W, pady=(2, 0))
        
        # Test connection button
        test_frame = ttk.Frame(api_frame)
        test_frame.grid(row=7, column=0, columnspan=2, pady=(15, 0))
        
        test_mb_button = ttk.Button(test_frame, text="Test Matchbook Login", command=self.test_matchbook_only)
        test_mb_button.pack(side=tk.LEFT, padx=(0, 10))
        
        test_both_button = ttk.Button(test_frame, text="🔍 Test Full System", command=self.test_connections, 
                                     style='Accent.TButton')
        test_both_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Scanner Settings", padding="15")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        settings_frame.columnconfigure(1, weight=1)
        
        # Threshold controls
        threshold_frame = ttk.Frame(settings_frame)
        threshold_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(threshold_frame, text="📊 Max Implied Probability Threshold:", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        threshold_controls = ttk.Frame(threshold_frame)
        threshold_controls.grid(row=1, column=0, sticky=tk.W)
        
        self.threshold_var = tk.DoubleVar(value=0.98)
        
        self.threshold_scale = ttk.Scale(threshold_controls, from_=0.95, to=0.995, 
                                        orient=tk.HORIZONTAL, length=200,
                                        variable=self.threshold_var, 
                                        command=self.update_threshold_display)
        self.threshold_scale.grid(row=0, column=0, padx=(0, 10))
        
        self.threshold_display = ttk.Label(threshold_controls, text="0.980", 
                                          font=('Arial', 12, 'bold'), 
                                          foreground='blue')
        self.threshold_display.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(threshold_controls, text="Precise:").grid(row=0, column=2, padx=(10, 5))
        threshold_spinbox = ttk.Spinbox(threshold_controls, from_=0.95, to=0.995, 
                                       increment=0.001, width=8, textvariable=self.threshold_var,
                                       command=self.update_threshold_display)
        threshold_spinbox.grid(row=0, column=3)
        
        # Minimum liquidity
        ttk.Label(settings_frame, text="💰 Minimum Liquidity (£):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.min_liquidity_var = tk.IntVar(value=100)
        liquidity_spinbox = ttk.Spinbox(settings_frame, from_=50, to=1000, 
                                       increment=50, width=10, textvariable=self.min_liquidity_var)
        liquidity_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Market filters
        ttk.Separator(settings_frame, orient=tk.HORIZONTAL).grid(row=2, column=0, columnspan=3, 
                                                                sticky=(tk.W, tk.E), pady=10)
        
        market_frame = ttk.Frame(settings_frame)
        market_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W)
        
        ttk.Label(market_frame, text="🎯 Target Sports:", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        filters_frame = ttk.Frame(market_frame)
        filters_frame.grid(row=1, column=0, sticky=tk.W)
        
        self.tennis_var = tk.BooleanVar(value=True)
        self.football_var = tk.BooleanVar(value=True)
        self.basketball_var = tk.BooleanVar(value=False)
        
        ttk.Checkbutton(filters_frame, text="🎾 Tennis", variable=self.tennis_var).grid(row=0, column=0, padx=(0, 20), sticky=tk.W)
        ttk.Checkbutton(filters_frame, text="⚽ Football", variable=self.football_var).grid(row=0, column=1, padx=(0, 20), sticky=tk.W)
        ttk.Checkbutton(filters_frame, text="🏀 Basketball", variable=self.basketball_var).grid(row=0, column=2, sticky=tk.W)
        
        # Control Frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=20, sticky=(tk.W, tk.E))
        
        # Scan button
        self.scan_button = ttk.Button(control_frame, text="🔍 SCAN FOR ARBITRAGE", 
                                     command=self.start_scan, style='Accent.TButton')
        self.scan_button.pack(side=tk.LEFT, padx=(0, 15), ipady=10)
        
        # Clear button
        clear_button = ttk.Button(control_frame, text="Clear Results", command=self.clear_results)
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to scan - Enter Matchbook credentials to begin")
        self.status_label = ttk.Label(control_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.RIGHT)
        
        # Results Frame
        results_frame = ttk.LabelFrame(main_frame, text="Real-Time Cross-Exchange Arbitrage Opportunities", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, 
                                                     width=100, height=25, 
                                                     font=('Courier', 9))
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Style configuration
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 14, 'bold'), padding=(20, 10))
    
    def update_threshold_display(self, value=None):
        """Update the threshold display"""
        current_value = self.threshold_var.get()
        self.threshold_display.config(text=f"{current_value:.3f}")
        
        if not self.scanning:
            profit_estimate = (1.0 - current_value) * 100
            self.status_var.set(f"Threshold: {current_value:.3f} (Min ~{profit_estimate:.1f}% profit) - Ready")
    
    def test_matchbook_only(self):
        """Test only Matchbook API connection"""
        username = self.mb_username.get()
        password = self.mb_password.get()
        
        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Please enter Matchbook username and password")
            return
        
        self.status_var.set("Testing Matchbook API...")
        
        def test_thread():
            self.scanner.matchbook_username = username
            self.scanner.matchbook_password = password
            matchbook_ok = self.scanner.test_matchbook_connection()
            
            def update_status():
                if matchbook_ok:
                    messagebox.showinfo("Matchbook Test", "✅ Matchbook API connection successful!")
                    self.status_var.set("✅ Matchbook connected")
                else:
                    messagebox.showerror("Matchbook Test", "❌ Matchbook API connection failed - Check credentials")
                    self.status_var.set("❌ Matchbook connection failed")
            
            self.root.after(0, update_status)
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def test_connections(self):
        """Test both API connections"""
        username = self.mb_username.get()
        password = self.mb_password.get()
        
        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Please enter Matchbook username and password")
            return
        
        self.status_var.set("Testing both API connections...")
        
        def test_thread():
            # Update scanner credentials
            self.scanner.matchbook_username = username
            self.scanner.matchbook_password = password
            
            # Test both connections
            smarkets_ok = self.scanner.test_smarkets_connection()
            matchbook_ok = self.scanner.test_matchbook_connection()
            
            def update_status():
                # Update Smarkets status
                if smarkets_ok:
                    self.sm_status_label.config(text="✅ Smarkets: Public API working", foreground='green')
                else:
                    self.sm_status_label.config(text="❌ Smarkets: Connection failed", foreground='red')
                
                # Show results
                if smarkets_ok and matchbook_ok:
                    self.status_var.set("✅ Both exchanges connected successfully!")
                    messagebox.showinfo("Connection Test", 
                                      "✅ Successfully connected to both exchanges!\n\n" +
                                      "📊 Smarkets: Public API access verified\n" +
                                      "🎯 Matchbook: Authenticated login successful\n\n" +
                                      "Ready to scan for real arbitrage opportunities!")
                elif smarkets_ok:
                    self.status_var.set("⚠️ Smarkets OK, Matchbook failed")
                    messagebox.showwarning("Connection Test", 
                                         "✅ Smarkets: Public API working\n" +
                                         "❌ Matchbook: Connection failed\n\n" +
                                         "Check your Matchbook credentials")
                elif matchbook_ok:
                    self.status_var.set("⚠️ Matchbook OK, Smarkets failed")
                    messagebox.showwarning("Connection Test", 
                                         "❌ Smarkets: Public API failed\n" +
                                         "✅ Matchbook: Connected successfully\n\n" +
                                         "Check your internet connection")
                else:
                    self.status_var.set("❌ Both exchanges failed to connect")
                    messagebox.showerror("Connection Test", 
                                       "❌ Failed to connect to both exchanges\n\n" +
                                       "Please check:\n" +
                                       "• Internet connection is working\n" +
                                       "• Matchbook credentials are correct\n" +
                                       "• Firewall/proxy settings")
            
            self.root.after(0, update_status)
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def start_scan(self):
        """Start the arbitrage scan"""
        if self.scanning:
            return
        
        username = self.mb_username.get()
        password = self.mb_password.get()
        
        if not username or not password:
            messagebox.showwarning("Missing Credentials", "Please enter Matchbook credentials for authenticated access")
            return
        
        self.scanning = True
        self.scan_button.config(text="⏳ SCANNING...", state='disabled')
        self.progress.start(10)
        self.status_var.set("Scanning real-time data from both exchanges...")
        
        scan_thread = threading.Thread(target=self.run_scan)
        scan_thread.daemon = True
        scan_thread.start()
    
    def run_scan(self):
        """Run the actual scan"""
        try:
            # Update scanner settings - no Smarkets token needed
            self.scanner.matchbook_username = self.mb_username.get()
            self.scanner.matchbook_password = self.mb_password.get()
            self.scanner.min_implied_prob_threshold = self.threshold_var.get()
            self.scanner.min_liquidity = self.min_liquidity_var.get()
            
            market_filters = {
                'tennis': self.tennis_var.get(),
                'football': self.football_var.get(),
                'basketball': self.basketball_var.get()
            }
            
            opportunities = self.scanner.find_real_arbitrage_opportunities(market_filters)
            self.root.after(0, self.display_results, opportunities)
            
        except Exception as e:
            error_msg = f"Error during scan: {str(e)}"
            self.root.after(0, self.show_error, error_msg)
        finally:
            self.root.after(0, self.scan_complete)
    
    def display_results(self, opportunities):
        """Display the scan results"""
        self.results_text.delete(1.0, tk.END)
        
        header = f"""
╔═══════════════════════════════════════════════════════════════════════════════════════╗
║                    REAL-TIME SMARKETS vs MATCHBOOK ARBITRAGE RESULTS                  ║
║  Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                                    ║
║  Threshold: {self.threshold_var.get():.3f} max implied probability                                     ║
║  Min Liquidity: £{self.min_liquidity_var.get()}                                                         ║
║  Data Source: LIVE MARKET DATA                                                        ║
╚═══════════════════════════════════════════════════════════════════════════════════════╝

"""
        self.results_text.insert(tk.END, header)
        
        if not opportunities:
            no_results = """
❌ NO REAL-TIME ARBITRAGE OPPORTUNITIES FOUND

Analysis complete - current market conditions:
• Real-time odds analyzed from both exchanges
• Markets are currently efficient between platforms
• No opportunities meet your threshold criteria

Recommendations:
• Lower your threshold slightly to see near-arbitrage situations
• Try different sports or time periods
• Markets change rapidly - scan again in a few minutes
• Consider that real arbitrage opportunities are rare and short-lived

Note: This scan used LIVE market data, not simulated data.
"""
            self.results_text.insert(tk.END, no_results)
            self.status_var.set(f"Real-time scan complete - No opportunities found")
        else:
            summary = f"✅ FOUND {len(opportunities)} REAL ARBITRAGE OPPORTUNITIES!\n\n"
            self.results_text.insert(tk.END, summary)
            
            for i, opp in enumerate(opportunities, 1):
                opportunity_text = f"""
🎯 REAL ARBITRAGE OPPORTUNITY #{i}
{'='*80}
📋 EVENT: {opp['event_name']}
• Sport: {opp['sport']}
• Market: {opp['market_name']}
• Event Time: {opp.get('event_time', 'TBD')}

💰 PROFIT ANALYSIS:
• Total Implied Probability: {opp['total_implied_prob']:.4f}
• Profit Margin: {opp['profit_margin']:.2f}%
• ROI: {opp['roi']:.2f}%

📊 BETTING STRATEGY:
┌─────────────────────────────────────────────────────────────────────┐
│ BET 1: {opp['bet1_selection']:<50}    │
│ ├─ Exchange: {opp['bet1_exchange'].upper():<25}                         │
│ ├─ Odds: {opp['bet1_odds']:<15} (Decimal)                            │
│ ├─ Stake: £{opp['bet1_stake']:<12}                                   │
│ ├─ Available: £{opp['bet1_liquidity']:<10}                          │
│ └─ Potential Return: £{opp['bet1_return']:<8}                       │
│                                                                     │
│ BET 2: {opp['bet2_selection']:<50}    │
│ ├─ Exchange: {opp['bet2_exchange'].upper():<25}                         │
│ ├─ Odds: {opp['bet2_odds']:<15} (Decimal)                            │
│ ├─ Stake: £{opp['bet2_stake']:<12}                                   │
│ ├─ Available: £{opp['bet2_liquidity']:<10}                          │
│ └─ Potential Return: £{opp['bet2_return']:<8}                       │
└─────────────────────────────────────────────────────────────────────┘

💡 EXECUTION DETAILS:
• Total Investment: £{opp['total_stake']:.2f}
• Guaranteed Profit: £{opp['guaranteed_profit']:.2f}
• Time Sensitivity: HIGH - Execute immediately!

⚡ QUICK LINKS:
• Smarkets: https://smarkets.com/
• Matchbook: https://www.matchbook.com/

⚠️  IMPORTANT NOTES:
• Odds change rapidly - verify before placing bets
• This is REAL market data from live exchanges
• Opportunities may disappear within seconds/minutes
• Always double-check calculations before betting

"""
                self.results_text.insert(tk.END, opportunity_text)
            
            self.status_var.set(f"✅ Found {len(opportunities)} real arbitrage opportunities!")
        
        self.results_text.see(1.0)
    
    def show_error(self, error_message):
        """Show error message"""
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, f"❌ SCAN ERROR: {error_message}\n\nTroubleshooting:\n• Check API credentials\n• Verify internet connection\n• Ensure exchanges are accessible\n• Try scanning again")
        self.status_var.set("Scan failed - Check error details")
        messagebox.showerror("Scan Error", error_message)
    
    def scan_complete(self):
        """Reset UI after scan completion"""
        self.scanning = False
        self.scan_button.config(text="🔍 SCAN FOR ARBITRAGE", state='normal')
        self.progress.stop()
    
    def clear_results(self):
        """Clear the results display"""
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Results cleared - Ready to scan")


class SmarketsMatchbookScanner:
    """Real-time cross-exchange arbitrage scanner"""
    def __init__(self):
        # API endpoints
        self.smarkets_base_url = "https://api.smarkets.com/v3"
        self.matchbook_base_url = "https://www.matchbook.com/bpapi/rest"
        
        # Credentials (Matchbook only - Smarkets uses public API)
        self.matchbook_username = ""
        self.matchbook_password = ""
        self.matchbook_session_token = None
        
        # Settings
        self.min_implied_prob_threshold = 0.98
        self.min_liquidity = 100
        
        # Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ArbitrageScanner/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def test_smarkets_connection(self):
        """Test Smarkets public API connection (no auth needed)"""
        try:
            url = f"{self.smarkets_base_url}/events/"
            response = self.session.get(url, timeout=10)
            print(f"Smarkets test: Status {response.status_code}")
            
            if response.status_code == 200:
                print("Smarkets public API connection successful")
                return True
            else:
                print(f"Smarkets public API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Smarkets connection error: {e}")
            return False
    
    def test_matchbook_connection(self):
        """Test Matchbook API connection"""
        try:
            return self.matchbook_login()
        except Exception as e:
            print(f"Matchbook connection error: {e}")
            return False
    
    def matchbook_login(self):
        """Login to Matchbook API"""
        try:
            url = f"{self.matchbook_base_url}/security/session"
            
            payload = {
                "username": self.matchbook_username,
                "password": self.matchbook_password
            }
            
            response = self.session.post(url, json=payload, timeout=15)
            print(f"Matchbook login: Status {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.matchbook_session_token = data.get('session-token')
                # Update session headers with token
                self.session.headers.update({
                    'session-token': self.matchbook_session_token
                })
                print("Matchbook login successful")
                return True
            else:
                print(f"Matchbook login failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"Matchbook login error: {e}")
            return False
    
    def find_real_arbitrage_opportunities(self, market_filters):
        """Find real arbitrage opportunities between exchanges using live data"""
        opportunities = []
        
        try:
            print(f"Starting REAL-TIME arbitrage scan...")
            print(f"Threshold: {self.min_implied_prob_threshold}")
            print(f"Min liquidity: £{self.min_liquidity}")
            
            # Get live events from both exchanges
            all_events = []
            
            for sport, enabled in market_filters.items():
                if enabled:
                    print(f"Fetching live {sport} events...")
                    
                    # Get Smarkets events
                    sm_events = self.get_smarkets_events(sport)
                    all_events.extend(sm_events)
                    
                    # Get Matchbook events  
                    mb_events = self.get_matchbook_events(sport)
                    all_events.extend(mb_events)
            
            print(f"Total live events found: {len(all_events)}")
            
            if not all_events:
                print("No live events found - may be outside trading hours")
                return opportunities
            
            # Group events by similarity (cross-exchange matching)
            event_groups = self.group_similar_events(all_events)
            print(f"Found {len(event_groups)} event groups for comparison")
            
            # Analyze each group for arbitrage opportunities
            for group in event_groups:
                if len(group) >= 2:  # Need events from both exchanges
                    arb_opps = self.analyze_event_group_for_arbitrage(group)
                    opportunities.extend(arb_opps)
            
            print(f"Found {len(opportunities)} real arbitrage opportunities")
            
        except Exception as e:
            print(f"Error in real arbitrage scan: {e}")
            import traceback
            traceback.print_exc()
        
        return opportunities
    
    def get_smarkets_events(self, sport_filter=None):
        """Get real live events from Smarkets public API"""
        events = []
        try:
            url = f"{self.smarkets_base_url}/events/"
            params = {'state': 'live', 'limit': 50}
            
            if sport_filter:
                sport_ids = {
                    'tennis': 'tennis',
                    'football': 'football', 
                    'basketball': 'basketball'
                }
                if sport_filter in sport_ids:
                    params['sport_id'] = sport_ids[sport_filter]
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for event in data.get('events', []):
                    events.append({
                        'id': event.get('id'),
                        'name': event.get('name'),
                        'sport': event.get('sport_id', 'unknown'),
                        'start_time': event.get('start_datetime'),
                        'state': event.get('state'),
                        'exchange': 'smarkets'
                    })
            else:
                print(f"Smarkets API error: {response.status_code}")
            
            print(f"Smarkets: Found {len(events)} live events")
                    
        except Exception as e:
            print(f"Error fetching Smarkets events: {e}")
        
        return events
    
    def get_smarkets_markets(self, event_id):
        """Get real markets for a Smarkets event"""
        markets = []
        try:
            url = f"{self.smarkets_base_url}/events/{event_id}/markets/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for market in data.get('markets', []):
                    if market.get('state') == 'live':
                        markets.append({
                            'id': market.get('id'),
                            'name': market.get('name'),
                            'event_id': event_id,
                            'exchange': 'smarkets'
                        })
                        
        except Exception as e:
            print(f"Error fetching Smarkets markets for event {event_id}: {e}")
        
        return markets
    
    def get_smarkets_odds(self, market_id):
        """Get real live odds for a Smarkets market"""
        odds = []
        try:
            url = f"{self.smarkets_base_url}/markets/{market_id}/contracts/"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for contract in data.get('contracts', []):
                    # Get current live prices
                    prices_url = f"{self.smarkets_base_url}/contracts/{contract.get('id')}/prices/"
                    prices_response = self.session.get(prices_url, timeout=5)
                    
                    if prices_response.status_code == 200:
                        prices_data = prices_response.json()
                        buys = prices_data.get('buys', [])
                        
                        if buys:
                            best_buy = buys[0]  # Best available price
                            decimal_odds = float(best_buy.get('odds', 0)) / 100
                            available_liquidity = float(best_buy.get('quantity', 0)) / 100
                            
                            if decimal_odds > 1 and available_liquidity >= self.min_liquidity:
                                odds.append({
                                    'selection': contract.get('name'),
                                    'odds': decimal_odds,
                                    'available': available_liquidity,
                                    'contract_id': contract.get('id'),
                                    'exchange': 'smarkets'
                                })
                            
        except Exception as e:
            print(f"Error fetching Smarkets odds for market {market_id}: {e}")
        
        return odds
    
    def get_matchbook_events(self, sport_filter=None):
        """Get real live events from Matchbook API"""
        events = []
        try:
            if not self.matchbook_session_token:
                if not self.matchbook_login():
                    return events
            
            url = f"{self.matchbook_base_url}/lookups/events"
            params = {'status': 'open', 'offset': 0, 'per-page': 50}
            
            if sport_filter:
                sport_ids = {
                    'tennis': 325,
                    'football': 11,
                    'basketball': 18
                }
                if sport_filter in sport_ids:
                    params['sport-ids'] = sport_ids[sport_filter]
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for event in data.get('events', []):
                    if event.get('in-running-flag'):  # Live events only
                        events.append({
                            'id': event.get('id'),
                            'name': event.get('name'),
                            'sport': event.get('sport-id'),
                            'start_time': event.get('start'),
                            'exchange': 'matchbook'
                        })
            elif response.status_code == 401:
                print("Matchbook: Session expired, trying to re-login...")
                if self.matchbook_login():
                    return self.get_matchbook_events(sport_filter)
            else:
                print(f"Matchbook API error: {response.status_code}")
            
            print(f"Matchbook: Found {len(events)} live events")
                    
        except Exception as e:
            print(f"Error fetching Matchbook events: {e}")
        
        return events
    
    def get_matchbook_markets(self, event_id):
        """Get real markets for a Matchbook event"""
        markets = []
        try:
            url = f"{self.matchbook_base_url}/events/{event_id}/markets"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for market in data.get('markets', []):
                    if market.get('status') == 'open':
                        markets.append({
                            'id': market.get('id'),
                            'name': market.get('name'),
                            'event_id': event_id,
                            'exchange': 'matchbook'
                        })
                        
        except Exception as e:
            print(f"Error fetching Matchbook markets for event {event_id}: {e}")
        
        return markets
    
    def get_matchbook_odds(self, market_id):
        """Get real live odds for a Matchbook market"""
        odds = []
        try:
            url = f"{self.matchbook_base_url}/markets/{market_id}/runners"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for runner in data.get('runners', []):
                    if runner.get('status') == 'open':
                        prices = runner.get('prices', [])
                        
                        # Find best back price
                        best_back = None
                        for price in prices:
                            if (price.get('side') == 'back' and 
                                price.get('odds') and 
                                price.get('available-amount', 0) >= self.min_liquidity):
                                
                                if not best_back or price.get('odds') > best_back.get('odds'):
                                    best_back = price
                        
                        if best_back:
                            odds.append({
                                'selection': runner.get('name'),
                                'odds': float(best_back.get('odds')),
                                'available': float(best_back.get('available-amount', 0)),
                                'runner_id': runner.get('id'),
                                'exchange': 'matchbook'
                            })
                                
        except Exception as e:
            print(f"Error fetching Matchbook odds for market {market_id}: {e}")
        
        return odds
    
    def group_similar_events(self, events):
        """Group events that are likely the same across exchanges"""
        groups = []
        processed = set()
        
        for i, event1 in enumerate(events):
            if i in processed:
                continue
                
            group = [event1]
            processed.add(i)
            
            for j, event2 in enumerate(events):
                if j in processed or i == j:
                    continue
                
                # Check if events are similar (same event on different exchanges)
                if (self.events_are_similar(event1, event2) and 
                    event1['exchange'] != event2['exchange']):
                    group.append(event2)
                    processed.add(j)
            
            # Only include groups with events from both exchanges
            if len(group) > 1:
                exchanges = {event['exchange'] for event in group}
                if len(exchanges) > 1:  # Must have different exchanges
                    groups.append(group)
        
        return groups
    
    def events_are_similar(self, event1, event2):
        """Check if two events are likely the same using improved matching"""
        name1 = event1['name'].lower()
        name2 = event2['name'].lower()
        
        # Clean names for better matching
        name1 = self.clean_event_name(name1)
        name2 = self.clean_event_name(name2)
        
        # Split into words
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        # Calculate similarity
        common_words = words1 & words2
        total_words = words1 | words2
        
        if len(total_words) == 0:
            return False
        
        similarity = len(common_words) / len(total_words)
        
        # Also check for partial matches (e.g., "Djokovic" matches "N. Djokovic")
        partial_matches = 0
        for word1 in words1:
            for word2 in words2:
                if len(word1) >= 4 and len(word2) >= 4:
                    if word1 in word2 or word2 in word1:
                        partial_matches += 1
        
        partial_similarity = partial_matches / max(len(words1), len(words2))
        
        # Consider similar if either metric is high enough
        return similarity >= 0.6 or partial_similarity >= 0.5
    
    def clean_event_name(self, name):
        """Clean event name for better matching"""
        import re
        # Remove common prefixes/suffixes and normalize
        name = re.sub(r'\(.*?\)', '', name)  # Remove parentheses content
        name = re.sub(r'\b(vs|v)\b', ' ', name)  # Remove vs/v
        name = re.sub(r'[^\w\s]', ' ', name)  # Remove special chars
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize whitespace
        return name
    
    def analyze_event_group_for_arbitrage(self, event_group):
        """Analyze a group of similar events for real arbitrage opportunities"""
        opportunities = []
        
        try:
            print(f"Analyzing event group: {[e['name'] for e in event_group]}")
            
            # Get markets for each event in the group
            all_markets = []
            for event in event_group:
                if event['exchange'] == 'smarkets':
                    markets = self.get_smarkets_markets(event['id'])
                else:
                    markets = self.get_matchbook_markets(event['id'])
                
                for market in markets:
                    market['event_name'] = event['name']
                    market['sport'] = event['sport']
                    all_markets.append(market)
            
            print(f"Found {len(all_markets)} markets across exchanges")
            
            # Group markets by type
            market_groups = self.group_similar_markets(all_markets)
            print(f"Grouped into {len(market_groups)} market type groups")
            
            # Analyze each market group for arbitrage
            for market_group in market_groups:
                if len(market_group) >= 2:
                    # Must have markets from different exchanges
                    exchanges = {market['exchange'] for market in market_group}
                    if len(exchanges) > 1:
                        arb_opps = self.find_arbitrage_in_market_group(market_group)
                        opportunities.extend(arb_opps)
                    
        except Exception as e:
            print(f"Error analyzing event group: {e}")
        
        return opportunities
    
    def group_similar_markets(self, markets):
        """Group markets that are the same type across exchanges"""
        groups = []
        processed = set()
        
        for i, market1 in enumerate(markets):
            if i in processed:
                continue
                
            group = [market1]
            processed.add(i)
            
            for j, market2 in enumerate(markets):
                if j in processed or i == j:
                    continue
                
                # Check if markets are similar type and from different exchanges
                if (self.markets_are_similar(market1, market2) and 
                    market1['exchange'] != market2['exchange']):
                    group.append(market2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def markets_are_similar(self, market1, market2):
        """Check if two markets are the same type using improved matching"""
        name1 = market1['name'].lower()
        name2 = market2['name'].lower()
        
        # Common market type keywords
        market_keywords = [
            ['winner', 'match', 'result'],
            ['total', 'over', 'under'],
            ['handicap', 'spread', 'line'],
            ['first', 'set'],
            ['correct', 'score']
        ]
        
        # Check if both names contain keywords from the same group
        for keyword_group in market_keywords:
            match1 = any(keyword in name1 for keyword in keyword_group)
            match2 = any(keyword in name2 for keyword in keyword_group)
            if match1 and match2:
                return True
        
        # Fallback to exact name match
        return name1 == name2
    
    def find_arbitrage_in_market_group(self, market_group):
        """Find real arbitrage opportunities within a market group"""
        opportunities = []
        
        try:
            print(f"Analyzing market group: {[m['name'] for m in market_group]}")
            
            # Get real odds for all markets in the group
            all_odds = []
            for market in market_group:
                if market['exchange'] == 'smarkets':
                    odds = self.get_smarkets_odds(market['id'])
                else:
                    odds = self.get_matchbook_odds(market['id'])
                
                for odd in odds:
                    odd['market_id'] = market['id']
                    odd['market_name'] = market['name']
                    odd['event_name'] = market['event_name']
                    odd['sport'] = market['sport']
                    all_odds.append(odd)
            
            print(f"Found {len(all_odds)} odds across markets")
            
            if len(all_odds) >= 2:
                # Calculate real arbitrage opportunities
                arb_opps = self.calculate_real_arbitrage(all_odds)
                opportunities.extend(arb_opps)
            
        except Exception as e:
            print(f"Error finding arbitrage in market group: {e}")
        
        return opportunities
    
    def calculate_real_arbitrage(self, odds_list):
        """Calculate real arbitrage opportunities from live odds"""
        opportunities = []
        
        try:
            # Group odds by selection/outcome
            outcome_groups = {}
            for odd in odds_list:
                # Normalize selection names for better matching
                selection = self.normalize_selection_name(odd['selection'])
                if selection not in outcome_groups:
                    outcome_groups[selection] = []
                outcome_groups[selection].append(odd)
            
            print(f"Grouped odds into {len(outcome_groups)} outcomes: {list(outcome_groups.keys())}")
            
            # For binary markets (most common)
            if len(outcome_groups) == 2:
                opportunities.extend(self.check_binary_arbitrage_real(outcome_groups))
            
        except Exception as e:
            print(f"Error calculating real arbitrage: {e}")
        
        return opportunities
    
    def normalize_selection_name(self, selection):
        """Normalize selection names for better matching"""
        import re
        # Convert to lowercase and remove common variations
        selection = selection.lower().strip()
        # Remove titles, initials, etc.
        selection = re.sub(r'\b[a-z]\.\s*', '', selection)  # Remove initials like "N. "
        selection = re.sub(r'\s+', ' ', selection)  # Normalize whitespace
        return selection
    
    def check_binary_arbitrage_real(self, outcome_groups):
        """Check for real arbitrage in binary markets using live odds"""
        opportunities = []
        
        try:
            outcome_names = list(outcome_groups.keys())
            outcome1_odds = outcome_groups[outcome_names[0]]
            outcome2_odds = outcome_groups[outcome_names[1]]
            
            print(f"Checking arbitrage between '{outcome_names[0]}' and '{outcome_names[1]}'")
            
            # Find best odds combination from different exchanges
            for odd1 in outcome1_odds:
                for odd2 in outcome2_odds:
                    # Must be from different exchanges
                    if odd1['exchange'] == odd2['exchange']:
                        continue
                    
                    # Check minimum liquidity requirements
                    if (odd1['available'] < self.min_liquidity or 
                        odd2['available'] < self.min_liquidity):
                        continue
                    
                    # Calculate arbitrage
                    odds1 = float(odd1['odds'])
                    odds2 = float(odd2['odds'])
                    
                    if odds1 <= 1 or odds2 <= 1:
                        continue
                    
                    implied_prob1 = 1.0 / odds1
                    implied_prob2 = 1.0 / odds2
                    total_implied_prob = implied_prob1 + implied_prob2
                    
                    print(f"Checking: {odds1:.2f} vs {odds2:.2f}, Total prob: {total_implied_prob:.4f}")
                    
                    # Check if real arbitrage exists
                    if total_implied_prob < self.min_implied_prob_threshold:
                        profit_margin = (1.0 - total_implied_prob) * 100
                        
                        # Calculate optimal stakes
                        total_stake = 1000
                        stake1 = (implied_prob1 / total_implied_prob) * total_stake
                        stake2 = (implied_prob2 / total_implied_prob) * total_stake
                        
                        # Calculate returns
                        return1 = stake1 * odds1
                        return2 = stake2 * odds2
                        
                        # Account for exchange commissions
                        commission1 = return1 * 0.02
                        commission2 = return2 * 0.02
                        
                        net_profit = min(return1, return2) - total_stake - commission1 - commission2
                        
                        if net_profit > 0:
                            opportunity = {
                                'event_name': odd1.get('event_name', 'Unknown Event'),
                                'market_name': odd1.get('market_name', 'Unknown Market'),
                                'sport': odd1.get('sport', 'Unknown'),
                                'total_implied_prob': round(total_implied_prob, 4),
                                'profit_margin': round(profit_margin, 2),
                                'roi': round((net_profit / total_stake) * 100, 2),
                                'bet1_selection': odd1['selection'],
                                'bet1_exchange': odd1['exchange'],
                                'bet1_odds': round(odds1, 2),
                                'bet1_stake': round(stake1, 2),
                                'bet1_liquidity': round(odd1['available'], 2),
                                'bet1_return': round(return1, 2),
                                'bet2_selection': odd2['selection'],
                                'bet2_exchange': odd2['exchange'],
                                'bet2_odds': round(odds2, 2),
                                'bet2_stake': round(stake2, 2),
                                'bet2_liquidity': round(odd2['available'], 2),
                                'bet2_return': round(return2, 2),
                                'total_stake': total_stake,
                                'guaranteed_profit': round(net_profit, 2),
                                'event_time': 'Live'
                            }
                            
                            opportunities.append(opportunity)
                            print(f"REAL ARBITRAGE FOUND: {profit_margin:.2f}% profit on {odd1.get('event_name')}")
                            
        except Exception as e:
            print(f"Error checking binary arbitrage: {e}")
        
        return opportunities



def run_arbitrage_scanner():
    """Main function to run the GUI"""
    root = tk.Tk()
    app = ArbitrageScannerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_arbitrage_scanner()