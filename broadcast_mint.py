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

def main():
    key = os.getenv("GUARDIAN_ORACLE_KEY")
    if not key:
        print("Missing key")
        return

    # ======== EDIT THESE TWO LINES ========
    contract_addr = "0xYOUR_REAL_CONTRACT_ADDRESS"   # <-- change
    # ======================================

    try:
        with open("abi.json") as f:
            abi = json.load(f)
    except:
        print("abi.json missing or invalid JSON.")
        return

    with open("market_manifest.json") as f:
        manifest = json.load(f)

    w3 = get_web3()
    contract = w3.eth.contract(address=contract_addr, abi=abi)
    account = w3.eth.account.from_key(key)

    # Find mint function
    mint_funcs = [f for f in abi if f.get('type') == 'function' and 'mint' in f.get('name', '').lower()]
    if not mint_funcs:
        print("No mint function in ABI. Available functions:")
        for f in abi:
            if f.get('type') == 'function':
                print(f"  - {f.get('name')}")
        return

    func = mint_funcs[0]
    func_name = func['name']
    inputs = func.get('inputs', [])

    # Build arguments (adjust if needed)
    args = []
    for inp in inputs:
        t = inp['type']
        if 'bytes32' in t:
            args.append("0x0000000000000000000000000000000000000000000000000000000000000000")
        elif 'uint' in t or 'int' in t:
            # if 18 decimals, adjust if not
            args.append(int(manifest.get('total_verified_tonnes', 0) * 1e18))
        elif 'address' in t:
            args.append(manifest.get('seller_wallet', contract_addr))
        elif 'string' in t:
            args.append("")   # adjust if you need a specific string
        else:
            args.append("0x0")
        print(f"  {inp.get('name','arg')} ({t}) = {args[-1]}")

    nonce = w3.eth.get_transaction_count(account.address)
    tx = contract.functions[func_name](*args).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
        "chainId": w3.eth.chain_id,
    })

    print(f"Sending {func_name}...")
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Tx sent: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status:
        print("🎉 Success! Payout sent.")
    else:
        print("❌ Reverted. Check arguments and ABI.")

if __name__ == "__main__":
    main()
