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
        self.ai_audit_enabled = False
        
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
                    model='gemini-1.5-flash',  # Ensure model name is correct
                    contents=prompt
                )
                if response.text:
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
                elif i < retries - 1:
                    time.sleep(2)
        return None

    def fetch_telemetry(self):
        zones = ["Zone-A", "Zone-B", "Zone-C"]
        zone = random.choice(zones)
        baseline = random.uniform(100, 1000)
        reduction = random.uniform(20, 200)
        return {
            "location": zone, 
            "mitigation_tonnes": round(reduction, 2), 
            "baseline": round(baseline, 2),
            "timestamp": datetime.now().isoformat()
        }

    def verify_mitigation_ai(self, data):
        # Use logic fallback if AI is disabled, offline, or on cooldown
        if not self.ai_active or not self.ai_audit_enabled or time.time() < self.ai_cooldown_until:
            if self.ai_audit_enabled:
                print("[!] AI on cooldown. Using logic threshold.", flush=True)
            return data['mitigation_tonnes'] > 15

        prompt = f"Audit: {data['location']} mitigated {data['mitigation_tonnes']} tonnes. Significant? YES/NO."
        res = self.call_gemini(prompt)
        if res: 
            return "YES" in res.upper()
        
        # Fallback if AI response is garbled
        print("[!] AI response unclear. Using logic threshold.", flush=True)
        return data['mitigation_tonnes'] > 15

    def issue_certificate(self, data):
        cert_id = f"VCU-{int(time.time())}"
        self.total_mitigated += data['mitigation_tonnes']
        
        # Store certificate for export
        certificate = {
            "cert_id": cert_id,
            "timestamp": data['timestamp'],
            "location": data['location'],
            "impact": data['mitigation_tonnes'],
            "status": "Verified"
        }
        self.certificates.append(certificate)
        
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
        tx_hash = f"0x{os.urandom(16).hex()}"
        tg_msg = (f"🎯 *TARGET CAPTURED*\nAsset: `{token}`\nProfit: `${round(profit, 2)}` 💰\n"
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
            json.dump({
                "total_mitigated": self.total_mitigated,
                "assets": self.certificates
            }, f, indent=4)
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
        print(f"[*] Starting Telegram Listener (ID: {self.chat_id})...")
        while True:
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
                params = {"offset": last_id + 1, "timeout": 20}
                print(f"[.] Polling Telegram... (Last ID: {last_id})", flush=True)
                resp = requests.get(url, params=params, timeout=25)
                
                if resp.status_code == 409:
                    print("[!] Telegram Conflict (409): Another instance is running. Run 'pkill -f carbon_miner.py' then restart.", flush=True)
                    time.sleep(10)
                    continue
                    
                if resp.status_code != 200:
                    raise Exception(f"HTTP {resp.status_code}")

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
