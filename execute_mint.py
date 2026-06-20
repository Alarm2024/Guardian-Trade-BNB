import os
import json
from web3 import Web3

def run_oracle_mint():
    # Securely fetch private key from environment
    private_key = os.getenv("GUARDIAN_ORACLE_KEY")
    if not private_key:
        print("[Error] GUARDIAN_ORACLE_KEY environment variable is not set.")
        print("Please run: export GUARDIAN_ORACLE_KEY='your_private_key'")
        return

    manifest_path = "market_manifest.json"
    contract_address = "0x08312f8381f059f5a8a13236CF10b54c08f9C991" 
    rpc_url = "https://rpc.ankr.com/eth" 

    # Connect to network
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("[Error] Cannot connect to blockchain network via RPC.")
        return

    print("[Success] Connected to blockchain network.")

    # Load manifest data
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    except FileNotFoundError:
        print(f"[Error] {manifest_path} file not found.")
        return

    account = w3.eth.account.from_key(private_key)
    contract_abi = [
        {
            "inputs": [
                {"internalType": "string", "name": "_certId", "type": "string"},
                {"internalType": "address", "name": "_beneficiary", "type": "address"},
                {"internalType": "string", "name": "_location", "type": "string"},
                {"internalType": "uint256", "name": "_tonnes", "type": "uint256"}
            ],
            "name": "registerAndMintVCU",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        }
    ]
    
    contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=contract_abi)

    print(f"Oracle Account Address: {account.address}")
    print(f"Total Verified Tonnes to Process: {manifest.get('total_verified_tonnes')}")

    # Process first asset as a validation test
    assets = manifest.get("assets", [])
    if assets:
        asset = assets[0]
        cert_id = asset["cert_id"]
        beneficiary = asset["beneficiary_wallet"]
        location = asset["impact"]["location"]
        tonnes = int(float(asset["impact"]["mitigation_tonnes"]))

        print(f"Preparing test transaction for Certificate: {cert_id}")
        
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.registerAndMintVCU(
            cert_id,
            Web3.to_checksum_address(beneficiary),
            location,
            tonnes
        ).build_transaction({
            'chainId': 1,
            'gas': 150000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        print("[Success] Transaction successfully structured and signed locally using environment key.")
    else:
        print("[Error] No assets found in manifest.")

if __name__ == "__main__":
    run_oracle_mint()
