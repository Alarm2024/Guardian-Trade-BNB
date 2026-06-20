import time
import os
import requests
from web3 import Web3
from logger import get_logger

# Initialize Logger
log = get_logger("OracleAgent")

# Configuration
RPC_ENDPOINT = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
CARBON_PRICE_THRESHOLD = 50.0 

CONTRACT_ABI = [
    {"inputs": [{"internalType": "uint256", "name": "awardId", "type": "uint256"}], "name": "distributeAward", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

def get_carbon_price():
    try:
        return 55.0 # Mocking price
    except Exception as e:
        log.error(f"Failed to fetch carbon price: {e}")
        return 0.0

def manage_protocol():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    
    log.info(f"Oracle Agent active as {account.address}")

    while True:
        try:
            price = get_carbon_price()
            log.info(f"Current Carbon Price: ${price}")

            if price >= CARBON_PRICE_THRESHOLD:
                log.info("Market favorable. Triggering distribution.")
                nonce = w3.eth.get_transaction_count(account.address)
                tx = contract.functions.distributeAward(0).build_transaction({
                    'chainId': 31337,
                    'gas': 200000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': nonce,
                })
                signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                log.info(f"Distribution triggered! Hash: {w3.to_hex(tx_hash)}")
        except Exception as e:
            log.error(f"Error in oracle loop: {e}")
            time.sleep(30)

        time.sleep(60)

if __name__ == "__main__":
    manage_protocol()
