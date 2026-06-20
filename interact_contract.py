import json
from web3 import Web3

def interact_with_contract(manifest_path, contract_address, rpc_url, private_key):
    # Initialize Web3 connection
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        print("Error: Failed to connect to the blockchain network.")
        return

    print("Connected to blockchain successfully.")
    
    # Load the manifest file
    try:
        with open(manifest_path, 'r') as file:
            manifest_data = json.load(file)
    except FileNotFoundError:
        print(f"Error: {manifest_path} not found.")
        return

    # Contract Minimal ABI for registration
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

    # Get account from private key
    account = w3.eth.account.from_key(private_key)
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)

    print(f"Processing transactions for contract: {contract_address}")
    print(f"Total Tonnes to sync: {manifest_data['total_verified_tonnes']}")

    # Process the first asset as a test batch
    if len(manifest_data['assets']) > 0:
        asset = manifest_data['assets'][0]
        cert_id = asset['cert_id']
        beneficiary = asset['beneficiary_wallet']
        location = asset['impact']['location']
        tonnes = int(asset['impact']['mitigation_tonnes'])

        print(f"Preparing Tx for Cert: {cert_id} | Beneficiary: {beneficiary}")

        # Build transaction payload
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.registerAndMintVCU(
            cert_id, beneficiary, location, tonnes
        ).build_transaction({
            'chainId': 1,  # Mainnet is 1, change if using Seplolia/Testnet
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })

        # Sign transaction locally
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        print("Transaction signed successfully. Ready for broadcast.")
        
        # To send transaction to the network, uncomment the lines below:
        # tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        # print(f"Transaction Broadcasted! Hash: {w3.to_hex(tx_hash)}")
    else:
        print("No assets found in manifest.")

# Configuration variables (Update with your live network details)
MANIFEST_FILE = "market_manifest.json"
CONTRACT_ADDR = "0x0000000000000000000000000000000000000000"
RPC_ENDPOINT = "https://rpc.ankr.com/eth"  # Replace with your Node provider URL
PRIV_KEY = "0x0000000000000000000000000000000000000000000000000000000000000000"

# Execute interaction script
interact_with_contract(MANIFEST_FILE, CONTRACT_ADDR, RPC_ENDPOINT, PRIV_KEY)
