import json
import os
from dotenv import load_dotenv

# Load environmental data
load_dotenv()

class Monetizer:
    """
    Carbon Asset Monetizer
    Converts 'Verified Mitigation Certificates' into a sellable marketplace manifest.
    """
    def __init__(self, report_file="market_manifest.json"):
        self.report_file = report_file
        self.market_price_per_tonne = 25.00  # Enterprise Carbon Credit Price (USD)

    def load_assets(self):
        if not os.path.exists(self.report_file):
            return []
        with open(self.report_file, "r") as f:
            data = json.load(f)
            # Handle both list format and the dictionary export format
            return data.get("assets", []) if isinstance(data, dict) else data

    def calculate_valuation(self, assets):
        # Handle different key names between live miner and historical logs
        total_tonnes = sum(asset.get('impact', {}).get('mitigation_tonnes', asset.get('impact', 0)) for asset in assets)
        total_value = total_tonnes * self.market_price_per_tonne
        return total_tonnes, total_value

    def generate_sales_manifest(self):
        assets = self.load_assets()
        if not assets:
            print("[!] No verified assets found to monetize.")
            return

        tonnes, value = self.calculate_valuation(assets)
        
        manifest = {
            "seller_wallet": "0x08312f8381f059f5a8a13236CF10b54c08f9C991",
            "total_verified_tonnes": round(tonnes, 2),
            "estimated_market_value_usd": round(value, 2),
            "currency": "USDC / ETH",
            "assets": assets,
            "verification_oracle": "Guardian Angel AI (Gemini 1.5-Flash)"
        }

        with open("market_manifest.json", "w") as f:
            json.dump(manifest, f, indent=4)

        print(f"\n--- MARKET MANIFEST GENERATED ---")
        print(f"💎 Total Assets: {len(assets)}")
        print(f"🌍 Total Impact: {round(tonnes, 2)} Tonnes CO2e")
        print(f"💰 Market Valuation: ${round(value, 2)} USD")
        print(f"---------------------------------")
        print("[✔] Manifest saved to market_manifest.json")
        print("[✔] Ready for OTC (Over-the-Counter) or DEX listing.")

if __name__ == "__main__":
    market = Monetizer()
    market.generate_sales_manifest()
