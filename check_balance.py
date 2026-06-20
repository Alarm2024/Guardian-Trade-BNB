import os, json
from web3 import Web3

def get_web3():
    for url in ["https://eth.llamarpc.com", "https://cloudflare-eth.com", "https://rpc.ankr.com/eth"]:
        try:
            w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
            if w3.is_connected():
                return w3
        except:
            pass
    raise Exception("No RPC")

# Load artifact directly
with open("/home/wyndhamdesert/out/GuardianAngelCarbon.sol/GuardianAngelCarbon.json") as f:
    artifact = json.load(f)

# Extract ABI
abi = artifact['abi']

# Extract contract address – find first valid address in networks or direct field
contract_addr = None
if 'networks' in artifact:
    for chain, info in artifact['networks'].items():
        if 'address' in info:
            contract_addr = info['address']
            break
if not contract_addr and 'address' in artifact:
    contract_addr = artifact['address']

if not contract_addr:
    raise Exception("No contract address found in artifact.")

# Convert to checksum address
w3 = get_web3()
contract_addr = w3.to_checksum_address(contract_addr)
print(f"Using contract: {contract_addr}")

SELLER_WALLET = "0x08312f8381f059f5a8a13236CF10b54c08f9C991"

contract = w3.eth.contract(address=contract_addr, abi=abi)

# Token info
try:
    name = contract.functions.name().call()
    symbol = contract.functions.symbol().call()
    decimals = contract.functions.decimals().call()
    print(f"Token: {name} ({symbol}), decimals: {decimals}")
except Exception as e:
    print(f"Could not fetch token metadata: {e}")
    decimals = 18
    symbol = "TOKEN"

# Balance
try:
    balance = contract.functions.balanceOf(SELLER_WALLET).call()
    print(f"Balance of {SELLER_WALLET}: {balance / (10 ** decimals):.4f} {symbol}")
except Exception as e:
    print(f"Error checking balance: {e}")
