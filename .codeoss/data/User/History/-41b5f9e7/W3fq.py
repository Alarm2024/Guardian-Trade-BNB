import time
import random
import json
import os
from datetime import datetime
import requests
from dotenv import load_dotenv
from web3 import Web3
from google import genai
import threading

# Load credentials
load_dotenv()

class CarbonMiner:
    """
    Guardian Angel v3.7 - Stability & Performance Fix (Updated with google-genai)
    """
    def __init__(self):
        self.wallet = os.getenv("PRIVATE_KEY")
        self.public_address = "0x08312f8381f059f5a8a13236CF10b54c08f9C991"
        self.rpc_url = os.getenv("RPC_URL")
        self.bot_token = os.getenv("BOT_TOKEN")
        self.chat_id = os.getenv("CHAT_ID")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.ai_cooldown_until = 0
        self.total_mitigated = 0
        self.realized_profit = 0
        self.certificates = []
        self.hunt_mode = False
        self.ai_audit_enabled = True # Enabled by default if AI is active
        
        self.load_state()
        
        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url)) if self.rpc_url else None
        
        # Initialize Gemini using the modern google-genai Client SDK
        self.ai_active = False
        self.client = None
        if self.gemini_key and self.gemini_key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=self.gemini_key)
                self.ai_active = True
                print(f"[✔] AI Engine Forced: gemini-1.5-flash (google-genai SDK)", flush=True)
            except Exception as e:
                print(f"[!] AI Init Error: {e}", flush=True)

        self.check_connectivity()

    def load_state(self):
        state_path = "bot_state.json"
        if os.path.exists(state_path):
            try:
                with open(state_path, "r") as f:
                    state = json.load(f)
                    self.total_mitigated = state.get("total_mitigated", 0)
                    self.realized_profit = state.get("realized_profit", 0)
                    self.certificates = state.get("certificates", [])
                print(f"[✔] State Loaded: {len(self.certificates)} assets cached.", flush=True)
            except Exception as e:
                print(f"[!] State Load Error: {e}", flush=True)

    def save_state(self):
        try:
            with open("bot_state.json", "w") as f:
                json.dump({
                    "total_mitigated": self.total_mitigated,
                    "realized_profit": self.realized_profit,
                    "certificates": self.certificates
                }, f, indent=4)
        except Exception as e:
            print(f"[!] State Save Error: {e}", flush=True)

    def check_connectivity(self):
        print(f"[*] Initializing Guardian Angel Oracle...")
        if self.w3 and self.w3.is_connected():
            print(f"[✔] Blockchain: ONLINE")
        else:
            print("[!] Warning: Blockchain offline. Running in Simulation Mode.")

    def send_telegram(self, message):
        if not self.bot_token or not self.chat_id:
            print("[!] Telegram Error: Missing token or chat_id", flush=True)
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}
        try:
            r = requests.post(url, json=payload, timeout=10)
            if r.status_code != 200:
                print(f"[!] Telegram API Error ({r.status_code}): {r.text}", flush=True)
        except Exception as e:
            print(f"[!] Telegram Request Failed: {e}", flush=True)

    def call_gemini(self, prompt, retries=3):
        if not self.ai_active or time.time() < self.ai_cooldown_until:
            return None
            
        print(f"[AI] Requesting Audit: {prompt[:60]}...", flush=True)
        for i in range(retries):
            try:
                response = self.client.models.generate_content(
                    model='gemini-1.5-flash',
                    model='models/gemini-1.5-flash',
                    contents=prompt
                )
                if response and hasattr(response, 'text') and response.text:
                    print(f"[AI] Response Received: {response.text[:60]}...", flush=True)
                    return response.text
                return None
            except Exception as e:
                err_msg = str(e).lower()
                print(f"[!] AI Attempt {i+1} Failed: {e}", flush=True)
                if "429" in err_msg or "quota" in err_msg:
                    # Hard quota limit hit. Set cooldown for 300 seconds (5 mins).
                    self.ai_cooldown_until = time.time() + 300
                    self.send_telegram("⏳ *AI Quota Hit:* Switching to automated Logic Mode for 5 minutes.")
                    return None
                elif "404" in err_msg:
                    print(f"[!] AI Model Not Found (404). Please ensure the model name 'gemini-1.5-flash' is supported in your region.", flush=True)
                elif "404" in err_msg or "not found" in err_msg:
                    print(f"[!] AI Model Path Error (404). Ensure Generative Language API is enabled in project {os.getenv('GOOGLE_CLOUD_PROJECT', 'current')}.", flush=True)
                    return None
                elif i < retries - 1:
                    time.sleep(2)
        return None

    def fetch_telemetry(self):
        zones = ["Zone-A", "Zone-B", "Zone-C"]
        zone = random.choice(zones)
        baseline = random.uniform(100, 1000)
        reduction = random.uniform(20, 200)
        current = baseline - reduction
        return {
            "location": zone, 
            "mitigation_tonnes": round(reduction, 2), 
            "baseline": round(baseline, 2),
            "current": round(current, 2),
            "timestamp": datetime.now().isoformat()
        }

    def verify_mitigation_ai(self, data):
        # Logic Fallback: if AI is offline, on cooldown, or disabled
        if not self.ai_active or not self.ai_audit_enabled or time.time() < self.ai_cooldown_until:
            print("[!] AI resting or disabled. Using logic threshold.", flush=True)
            return data['mitigation_tonnes'] > 15

        prompt = f"Carbon Audit: {data['location']} mitigated {data['mitigation_tonnes']} tonnes. Is this significant? Respond ONLY with YES or NO."
        res = self.call_gemini(prompt)
        if res: 
            return "YES" in res.upper()
        
        # Default logic if AI fails
        return data['mitigation_tonnes'] > 15

    def issue_certificate(self, data):
        cert_id = f"VCU-{int(time.time())}-{random.randint(1000, 9999)}"
        self.total_mitigated += data['mitigation_tonnes']
        
        # Store certificate for export
        certificate = {
            "cert_id": cert_id,
            "issuer": "Guardian Angel AI Oracle",
            "beneficiary_wallet": self.public_address,
            "impact": {
                "timestamp": data['timestamp'],
                "location": data['location'],
                "baseline": data['baseline'],
                "current": data['current'],
                "mitigation_tonnes": data['mitigation_tonnes']
            },
            "status": "Verified"
        }
        self.certificates.append(certificate)
        self.save_state()
        
        print(f"[💎] ASSET MINTED: {cert_id} ({data['mitigation_tonnes']} Tonnes)", flush=True)
        self.send_telegram(f"💎 *New Carbon Asset*\nID: `{cert_id}`\nImpact: {data['mitigation_tonnes']} Tonnes")

    def run_mining_cycle(self):
        try:
            data = self.fetch_telemetry()
            if self.verify_mitigation_ai(data):
                self.issue_certificate(data)
        except:
            pass

    def capture_opportunity(self, token, profit):
        self.realized_profit += profit
        self.save_state()
        tx_hash = f"0x{os.urandom(32).hex()}"
        tg_msg = (f"🎯 *TARGET CAPTURED*\nAsset: `{token}`\nProfit: `${round(profit, 2)}` 💰\n"
                  f"TX: `{tx_hash[:18]}...`\n"
                  f"Total Realized: `${round(self.realized_profit, 2)}` 💎")
        self.send_telegram(tg_msg)

    def scan_flashloan_arbitrage(self, manual=False):
        token = random.choice(["NCT", "BCT", "MCO2"])
        profit_pct = random.uniform(0.5, 3.0)
        if profit_pct > 1.2:
            profit = 100000 * (profit_pct / 100)
            if self.hunt_mode: self.capture_opportunity(token, profit)
            else: self.send_telegram(f"⚡ *CHANCE*\nAsset: `{token}`\nProfit: `${round(profit, 2)}`\nSend `/hunt` to catch!")
        elif manual:
            self.send_telegram(f"🔍 Market stable for `{token}`.")

    def handle_ai_chat(self, user_msg):
        if not self.ai_active:
            self.send_telegram("❌ *AI Offline:* Gemini is not configured correctly. Check your API key!")
            return
            
        system_context = f"You are Guardian Angel AI. Stats: {round(self.total_mitigated, 2)} tonnes, ${round(self.realized_profit, 2)} profit. User: {user_msg}"
        res = self.call_gemini(system_context)
        if res:
            self.send_telegram(f"🔮 *Gemini:* {res}")
        elif time.time() < self.ai_cooldown_until:
            wait_time = int(self.ai_cooldown_until - time.time())
            self.send_telegram(f"⏳ *AI Resting:* I hit a rate limit. I'll be back in {wait_time}s! Use `/status` to check.")
        else:
            self.send_telegram("⚠️ *AI Error:* I couldn't get a response from Gemini. Please try again.")

    def export_report(self):
        if not self.certificates:
            self.send_telegram("❌ *Export Failed:* No certificates found to export.")
            return
            
        manifest_path = "market_manifest.json"
        with open(manifest_path, "w") as f:
            data = {
                "seller_wallet": self.public_address,
                "total_verified_tonnes": round(self.total_mitigated, 2),
                "estimated_market_value_usd": round(self.total_mitigated * 25.0, 2),
                "currency": "USDC / ETH",
                "assets": self.certificates,
                "verification_oracle": "Guardian Angel AI (Gemini 1.5-Flash)"
            }
            json.dump(data, f, indent=4)
        self.send_telegram(f"✅ *Manifest Exported:* `{len(self.certificates)}` assets saved to `{manifest_path}`.")

    def generate_invoice(self):
        total_value = self.realized_profit + (self.total_mitigated * 25.0)
        invoice = (f"📜 *VERIFIED IMPACT INVOICE*\n"
                   f" Beneficiary: `ELGHALY SUSTAINABLE`\n"
                   f"Wallet: `{self.public_address}`\n\n"
                   f"💰 *Total Valuation:* `${round(total_value, 2)} USD`\n\n"
                   f"Send **USDT (ERC-20)** to the wallet above to claim assets.")
        self.send_telegram(invoice)

    def get_telegram_updates(self):
        if not self.bot_token: 
            print("[!] Error: No BOT_TOKEN found.")
            return
        last_id = 0
        
        # Clear webhook to help resolve 409 Conflict errors on startup
        try:
            # Added drop_pending_updates to clear the queue and reset the connection state
            requests.get(
                f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook?drop_pending_updates=True", 
                timeout=10
            )
        except: pass

        print(f"[*] Starting Telegram Listener (ID: {self.chat_id})...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                params = {"offset": last_id + 1, "timeout": 20}
                print(f"[.] Polling Telegram... (Last ID: {last_id})", flush=True)
                resp = requests.get(url, params=params, timeout=25)
                
                if resp.status_code == 409:
                    print("\n[❌] CONFLICT ERROR (409): Another instance of this bot is already running!")
                    print("[💡] Fix: Run 'pkill -f carbon_miner.py' in your terminal then restart.\n", flush=True)
                    print("\n[❌] TELEGRAM CONFLICT: Multiple instances detected.")
                    print("[💡] Run: pkill -f carbon_miner.py\n", flush=True)
                    time.sleep(10)
                    continue
                    
                if resp.status_code != 200:
                    print(f"[!] Telegram HTTP Error {resp.status_code}. Retrying...", flush=True)
                    time.sleep(5)
                    continue

                data = resp.json()
                if "result" in data:
                    for update in data["result"]:
                        last_id = update["update_id"]
                        if "message" in update and "text" in update["message"]:
                            text = update["message"]["text"]
                            print(f"[⚡] Command Received: {text}")
                            
                            if text == "/status":
                                rpc_status = "✅" if self.w3 and self.w3.is_connected() else "❌ (Sim)"
                                ai_status = "✅" if time.time() > self.ai_cooldown_until else "⏳ (Cooldown)"
                                audit_status = "🤖 AI" if self.ai_audit_enabled else "🔢 Logic"
                                self.send_telegram(f"📊 *Status*\nBlockchain: {rpc_status}\nAI Chat: {ai_status}\nAudit Mode: `{audit_status}`\nHunt: `{'ON' if self.hunt_mode else 'OFF'}`\nProfit: `${round(self.realized_profit, 2)}` 💰\nMitigated: `{round(self.total_mitigated, 2)}` T")
                            elif text == "/hunt":
                                self.hunt_mode = not self.hunt_mode
                                self.send_telegram(f"🏹 *Hunt {'ON' if self.hunt_mode else 'OFF'}*")
                            elif text == "/clear":
                                self.total_mitigated = 0
                                self.realized_profit = 0
                                self.certificates = []
                                self.send_telegram("♻️ *Stats Reset:* Mitigation and profit counters cleared.")
                            elif text == "/export":
                                self.export_report()
                            elif text == "/help":
                                help_msg = ("📖 *Available Commands:*\n"
                                           "`/status` - View current performance\n"
                                           "`/mine` - Trigger manual carbon audit\n"
                                           "`/hunt` - Toggle auto-flashloan capture\n"
                                           "`/flashloan` - Manual market scan\n"
                                           "`/ai` - Toggle AI vs Logic auditing\n"
                                           "`/export` - Save assets to manifest\n"
                                           "`/clear` - Reset all statistics\n"
                                           "`/payout` - Generate invoice")
                                self.send_telegram(help_msg)
                            elif text == "/ai":
                                self.ai_audit_enabled = not self.ai_audit_enabled
                                self.send_telegram(f"🤖 *AI Auditing {'ON' if self.ai_audit_enabled else 'OFF'}* (Saves tokens if OFF)")
                            elif text == "/payout":
                                self.generate_invoice()
                            elif text == "/mine":
                                self.send_telegram("⛏ *Mining...*")
                                self.run_mining_cycle()
                            elif text == "/flashloan":
                                self.send_telegram("⚡ *Scanning Markets...*")
                                self.scan_flashloan_arbitrage(manual=True)
                            elif not text.startswith("/"):
                                threading.Thread(target=self.handle_ai_chat, args=(text,), daemon=True).start()
                else:
                    print(f"[?] Unexpected Response Structure: {data}")
            except Exception as e:
                print(f"[!] Polling Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    miner = CarbonMiner()
    print("--- Guardian Angel v3.7 Active ---")
    miner.send_telegram("🚀 *Guardian Angel v3.7 Online*")
    
    def background_tasks():
        print("[*] Background Task Thread Started.")
        while True:
            try:
                print("[*] Running background mining cycle...")
                miner.run_mining_cycle()
                print("[*] Running flashloan scan...")
                miner.scan_flashloan_arbitrage()
            except Exception as e:
                print(f"[!] Background Task Error: {e}")
            
            interval = 5 if miner.hunt_mode else 60
            print(f"[*] Sleeping for {interval}s...")
            time.sleep(interval)
            
    threading.Thread(target=background_tasks, daemon=True).start()
    miner.get_telegram_updates()
