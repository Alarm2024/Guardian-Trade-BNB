import os
from flask import Flask, request, jsonify
from carbon_miner import CarbonMiner
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
# eInitialize in API mode to avoid lock file and background thread conflicts
miner = CarbonMiner(is_api_instance=True)

@app.route('/verify', methods=['POST'])
def verify_impact():
    """
    API endpoint for companies to pay for AI-verified carbon reports.
    Input: { "location": "...", "baseline": 100, "current": 80 }
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Run the Gemini AI Audit
    print(f"[*] AI Audit requested for: {data.get('location')}")
    is_verified = miner.verify_mitigation_ai(data)
    
    report = {
        "status": "Verified" if is_verified else "Rejected",
        "verifier": "Guardian Angel AI (Gemini 1.5-Flash)",
        "audit_timestamp": datetime.now().isoformat(),
        "service_fee_usd": 5.00 # Example fee per audit
    }
    
    return jsonify(report)

@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "system": "Guardian Angel Carbon Oracle",
        "ai_engine": "Gemini 1.5-Flash (google-genai SDK)",
        "total_audits_performed": len(miner.certificates)
    })

if __name__ == "__main__":
    # In a real environment, we'd use a public tunnel like ngrok or serve on a public IP
    print("[*] Starting AI Environmental Audit API...")
    app.run(host='0.0.0.0', port=5000)
