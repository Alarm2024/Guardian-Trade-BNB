import time
import os
import google.generativeai as genai
from web3 import Web3
from logger import get_logger

# Initialize Logger
log = get_logger("ProposalMonitor")

# Configuration
RPC_ENDPOINT = "http://127.0.0.1:8545"
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# Load secure credentials
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
PRIVATE_KEY = os.environ.get("PRIVATE_KEY")
model = genai.GenerativeModel('gemini-1.5-flash')

# Minimal ABI... (ABI definition remains the same)
CONTRACT_ABI = [
    {"anonymous": False, "inputs": [{"indexed": True, "internalType": "bytes32", "name": "proposalId", "type": "bytes32"}, {"indexed": True, "internalType": "address", "name": "proposer", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "deadline", "type": "uint256"}], "name": "ChangeProposed", "type": "event"},
    {"inputs": [{"internalType": "bytes32", "name": "proposalId", "type": "bytes32"}], "name": "proposals", "outputs": [{"internalType": "bytes32", "name": "parameter", "type": "bytes32"}, {"internalType": "uint256", "name": "value", "type": "uint256"}, {"internalType": "uint256", "name": "deadline", "type": "uint256"}, {"internalType": "bool", "name": "executed", "type": "bool"}, {"internalType": "bool", "name": "approvedByOwner", "type": "bool"}, {"internalType": "bool", "name": "approvedByGuardian", "type": "bool"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "bytes32", "name": "proposalId", "type": "bytes32"}], "name": "approveProposal", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

def analyze_and_approve(proposal_id, proposal_data):
    try:
        prompt = f"Analyze this proposal for the GuardianAngelCarbon protocol: {proposal_data}. Should this proposal be approved to ensure protocol security and sustainability? Respond ONLY with 'APPROVE' or 'REJECT'."
        response = model.generate_content(prompt)
        return "APPROVE" in response.text.upper()
    except Exception as e:
        log.error(f"Gemini analysis failed: {e}")
        return False

def monitor_proposals():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)
    
    log.info(f"Monitoring proposals as {account.address}")
    event_filter = contract.events.ChangeProposed.create_filter(fromBlock='latest')

    while True:
        try:
            for event in event_filter.get_new_entries():
                proposal_id = event['args']['proposalId']
                log.info(f"New proposal detected: {proposal_id.hex()}")
                proposal_data = contract.functions.proposals(proposal_id).call()
                
                if analyze_and_approve(proposal_id, proposal_data):
                    log.info(f"Approving proposal {proposal_id.hex()}")
                    
                    nonce = w3.eth.get_transaction_count(account.address)
                    tx = contract.functions.approveProposal(proposal_id).build_transaction({
                        'chainId': 31337,
                        'gas': 200000,
                        'gasPrice': w3.eth.gas_price,
                        'nonce': nonce,
                    })
                    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    log.info(f"Approval transaction submitted: {w3.to_hex(tx_hash)}")
        except Exception as e:
            log.error(f"Error in monitor loop: {e}")
            time.sleep(30) # Backoff on error
                
        time.sleep(10)

if __name__ == "__main__":
    monitor_proposals()
