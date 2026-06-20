import json

def process_market_manifest(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    print("--- Manifest Overview ---")
    print(f"Seller Wallet: {data['seller_wallet']}")
    print(f"Total Tonnes: {data['total_verified_tonnes']} VCU")
    print(f"Market Value: ${data['estimated_market_value_usd']:,} USD\n")
    
    zones = {}
    for asset in data['assets']:
        zone = asset['impact']['location']
        mitigation = asset['impact']['mitigation_tonnes']
        if zone not in zones:
            zones[zone] = {'count': 0, 'total_tonnes': 0.0}
        zones[zone]['count'] += 1
        zones[zone]['total_tonnes'] += mitigation
        
    print("--- Next Phase Batches By Zone ---")
    for zone, stats in zones.items():
        print(f"[{zone}] -> Total Certificates: {stats['count']} | Total Volume: {stats['total_tonnes']:.2f} Tonnes")

process_market_manifest('market_manifest.json')
