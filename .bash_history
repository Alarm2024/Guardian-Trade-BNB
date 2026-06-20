                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"DeepSeek API error: {resp.status} - {error_text}")
                        return {"risk_level": "unknown", "reasoning": "API error", "recommendation": "reject"}
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    # Simple parsing – improve as needed
                    risk_level = "medium"
                    recommendation = "reject"
                    if "low" in content.lower():
                        risk_level = "low"
                        recommendation = "approve"
                    elif "medium" in content.lower():
                        risk_level = "medium"
                        recommendation = "reject" if "reject" in content.lower() else "approve"
                    else:
                        risk_level = "high"
                        recommendation = "reject"
                    return {
                        "risk_level": risk_level,
                        "reasoning": content,
                        "recommendation": recommendation
                    }
        except Exception as e:
            logger.error(f"DeepSeek request failed: {e}")
            return {"risk_level": "error", "reasoning": str(e), "recommendation": "reject"}
EOF

cat << 'EOF' > src/telegram_notifier.py
import aiohttp
from config.settings import settings
from utils.logging import setup_logging

logger = setup_logging()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, text: str) -> bool:
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info(f"Telegram message sent: {text[:50]}...")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"Telegram send error: {error}")
                        return False
        except Exception as e:
            logger.error(f"Telegram exception: {e}")
            return False

    async def notify_trade(self, token: str, action: str, reason: str, details: dict = None):
        msg = f"🔔 <b>Guardian Trade</b>\n"
        msg += f"Token: <code>{token}</code>\n"
        msg += f"Action: <b>{action}</b>\n"
        msg += f"Reason: {reason}\n"
        if details:
            msg += f"Details: <code>{details}</code>\n"
        await self.send_message(msg)
EOF

cat << 'EOF' > src/executor.py
from web3 import AsyncWeb3, AsyncHTTPProvider
from config.settings import settings
from utils.logging import setup_logging
from utils.helpers import to_checksum

logger = setup_logging()

EXECUTOR_ABI = [
    {
        "inputs": [
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "name": "swap",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "tokenOut", "type": "address"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "name": "swapWithBNB",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
]

class Executor:
    def __init__(self):
        self.w3 = AsyncWeb3(AsyncHTTPProvider(settings.BSC_RPC_URL))
        self.contract_address = to_checksum(settings.EXECUTION_CONTRACT_ADDRESS)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=EXECUTOR_ABI)
        self.account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)

    async def execute_swap_with_bnb(self, token_out: str, amount_in: int, path: list, slippage_bps: int = 100) -> str:
        token_out = to_checksum(token_out)
        amount_out_min = int(amount_in * (10000 - slippage_bps) / 10000)
        latest_block = await self.w3.eth.get_block('latest')
        deadline = int(latest_block['timestamp']) + 300

        nonce = await self.w3.eth.get_transaction_count(self.account.address)
        gas_price = await self.w3.eth.gas_price

        txn = await self.contract.functions.swapWithBNB(
            token_out,
            amount_out_min,
            deadline,
            path
        ).build_transaction({
            'from': self.account.address,
            'value': amount_in,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': gas_price,
        })

        signed = self.account.sign_transaction(txn)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        logger.info(f"Swap tx sent: {tx_hash.hex()}")
        receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            logger.info("Swap successful")
            return tx_hash.hex()
        else:
            logger.error(f"Swap failed: {receipt}")
            raise Exception("Swap transaction failed")
EOF

cat << 'EOF' > utils/helpers.py
from web3 import Web3

def to_checksum(address: str) -> str:
    return Web3.to_checksum_address(address)
EOF

cat << 'EOF' > src/orchestrator.py
import asyncio
from typing import Dict, Any
from src.security_validator import SecurityValidator
from src.ai_analyzer import AIAnalyzer
from src.telegram_notifier import TelegramNotifier
from src.executor import Executor
from utils.logging import setup_logging

logger = setup_logging()

class Orchestrator:
    def __init__(self):
        self.validator = SecurityValidator()
        self.ai_analyzer = AIAnalyzer()
        self.notifier = TelegramNotifier()
        self.executor = Executor()

    async def get_opportunity(self) -> Dict[str, Any]:
        # Mock opportunity – replace with real strategy
        return {
            "token_in": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",  # WBNB
            "token_out": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",  # CAKE
            "amount_in": 10**17,  # 0.1 BNB
            "path": [
                "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"
            ],
        }

    async def run(self):
        logger.info("Guardian‑Trade Agent started")
        while True:
            try:
                opportunity = await self.get_opportunity()
                token_out = opportunity["token_out"]
                amount_in = opportunity["amount_in"]
                path = opportunity["path"]

                # 1. Security validation
                valid, reason, details = await self.validator.validate(token_out)
                if not valid:
                    await self.notifier.notify_trade(token_out, "REJECTED", reason, details)
                    logger.warning(f"Trade rejected: {reason}")
                    await asyncio.sleep(60)
                    continue

                # 2. AI risk assessment
                token_data = {"address": token_out, "amount": amount_in}
                risk = await self.ai_analyzer.assess_risk(token_out, token_data)
                if risk["recommendation"] != "approve":
                    await self.notifier.notify_trade(token_out, "REJECTED (AI)", risk["reasoning"], risk)
                    logger.warning(f"AI rejected: {risk['reasoning']}")
                    await asyncio.sleep(60)
                    continue

                # 3. Execute swap
                logger.info(f"Executing swap for {token_out} with {amount_in} BNB")
                tx_hash = await self.executor.execute_swap_with_bnb(
                    token_out=token_out,
                    amount_in=amount_in,
                    path=path
                )
                await self.notifier.notify_trade(
                    token_out,
                    "EXECUTED",
                    f"Swap successful. TX: {tx_hash}",
                    {"amount": amount_in, "path": path}
                )
                logger.info(f"Trade executed: {tx_hash}")
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Orchestrator error: {e}", exc_info=True)
                await self.notifier.send_message(f"❌ Orchestrator error: {e}")
                await asyncio.sleep(10)
EOF

cat << 'EOF' > src/executor.py
from web3 import AsyncWeb3
from config.settings import settings

class Executor:
    def __init__(self):
        self.w3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(settings.BSC_RPC_URL))

    async def execute_swap_with_bnb(self, token_out: str, amount_in: int, path: list) -> str:
        # Placeholder for real transaction logic
        print(f"Simulating swap for {token_out} with {amount_in}")
        return "0xMockTransactionHash12345"
EOF

cat << 'EOF' > main.py
import asyncio
from src.orchestrator import Orchestrator
from utils.logging import setup_logging

logger = setup_logging()

if __name__ == "__main__":
    orchestrator = Orchestrator()
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
EOF

cat << 'EOF' > main.py
import asyncio
from src.orchestrator import Orchestrator
from utils.logging import setup_logging

logger = setup_logging()

if __name__ == "__main__":
    orchestrator = Orchestrator()
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully.")
EOF

cat << 'EOF' > src/orchestrator.py
import asyncio
from src.security_validator import SecurityValidator
from src.ai_analyzer import AIAnalyzer
from src.telegram_notifier import TelegramNotifier
from utils.logging import setup_logging

logger = setup_logging()

class Orchestrator:
    def __init__(self):
        self.validator = SecurityValidator()
        self.analyzer = AIAnalyzer()
        self.notifier = TelegramNotifier()

    async def run(self):
        logger.info("Guardian-Trade Agent started. Monitoring for tokens...")
        
        # This is a simple loop; in production, you'd integrate a scanner or websocket.
        # For testing, we can simulate an event or wait for a trigger.
        while True:
            try:
                # Placeholder for your token detection logic
                logger.info("Checking for new tokens...")
                await asyncio.sleep(60) # Wait for 60 seconds before next check
                
            except Exception as e:
                logger.error(f"Error in orchestrator loop: {e}")
                await asyncio.sleep(10)
EOF

python3 main.py
pip install --upgrade -r requirements.txt
cat << 'EOF' > requirements.txt
Web3==6.11.1
aiohttp==3.9.0
python-dotenv==1.0.0
eth-typing>=4.0.0
eth-utils>=3.0.0
loguru==0.7.2
openai==1.6.1
EOF

pip install --upgrade -r requirements.txt
cat << 'EOF' > src/orchestrator.py
import asyncio
from typing import Dict, Any
from src.security_validator import SecurityValidator
from src.ai_analyzer import AIAnalyzer
from src.telegram_notifier import TelegramNotifier
from src.executor import Executor
from utils.logging import setup_logging

logger = setup_logging()

class Orchestrator:
    def __init__(self):
        self.validator = SecurityValidator()
        self.ai_analyzer = AIAnalyzer()
        self.notifier = TelegramNotifier()
        self.executor = Executor()

    async def get_opportunity(self) -> Dict[str, Any]:
        # Mock opportunity – replace with real strategy
        return {
            "token_in": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",  # WBNB
            "token_out": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",  # CAKE
            "amount_in": 10**17,  # 0.1 BNB
            "path": [
                "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"
            ],
        }

    async def run(self):
        logger.info("Guardian‑Trade Agent started")
        while True:
            try:
                opportunity = await self.get_opportunity()
                token_out = opportunity["token_out"]
                amount_in = opportunity["amount_in"]
                path = opportunity["path"]

                # 1. Security validation
                valid, reason, details = await self.validator.validate(token_out)
                if not valid:
                    await self.notifier.notify_trade(token_out, "REJECTED", reason, details)
                    logger.warning(f"Trade rejected: {reason}")
                    await asyncio.sleep(60)
                    continue

                # 2. AI risk assessment
                token_data = {"address": token_out, "amount": amount_in}
                risk = await self.ai_analyzer.assess_risk(token_out, token_data)
                if risk["recommendation"] != "approve":
                    await self.notifier.notify_trade(token_out, "REJECTED (AI)", risk["reasoning"], risk)
                    logger.warning(f"AI rejected: {risk['reasoning']}")
                    await asyncio.sleep(60)
                    continue

                # 3. Execute swap
                logger.info(f"Executing swap for {token_out} with {amount_in} BNB")
                tx_hash = await self.executor.execute_swap_with_bnb(
                    token_out=token_out,
                    amount_in=amount_in,
                    path=path
                )
                await self.notifier.notify_trade(
                    token_out,
                    "EXECUTED",
                    f"Swap successful. TX: {tx_hash}",
                    {"amount": amount_in, "path": path}
                )
                logger.info(f"Trade executed: {tx_hash}")
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Orchestrator error: {e}", exc_info=True)
                await self.notifier.send_message(f"❌ Orchestrator error: {e}")
                await asyncio.sleep(10)
EOF

cat << 'EOF' > src/executor.py
from web3 import AsyncWeb3, AsyncHTTPProvider
from config.settings import settings
from utils.logging import setup_logging
from utils.helpers import to_checksum

logger = setup_logging()

EXECUTOR_ABI = [
    {
        "inputs": [
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "name": "swap",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "tokenOut", "type": "address"},
            {"name": "amountOutMin", "type": "uint256"},
            {"name": "deadline", "type": "uint256"},
            {"name": "path", "type": "address[]"},
        ],
        "name": "swapWithBNB",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    },
]

class Executor:
    def __init__(self):
        self.w3 = AsyncWeb3(AsyncHTTPProvider(settings.BSC_RPC_URL))
        self.contract_address = to_checksum(settings.EXECUTION_CONTRACT_ADDRESS)
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=EXECUTOR_ABI)
        self.account = self.w3.eth.account.from_key(settings.PRIVATE_KEY)

    async def execute_swap_with_bnb(self, token_out: str, amount_in: int, path: list, slippage_bps: int = 100) -> str:
        token_out = to_checksum(token_out)
        amount_out_min = int(amount_in * (10000 - slippage_bps) / 10000)
        latest_block = await self.w3.eth.get_block('latest')
        deadline = int(latest_block['timestamp']) + 300

        nonce = await self.w3.eth.get_transaction_count(self.account.address)
        gas_price = await self.w3.eth.gas_price

        txn = await self.contract.functions.swapWithBNB(
            token_out,
            amount_out_min,
            deadline,
            path
        ).build_transaction({
            'from': self.account.address,
            'value': amount_in,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': gas_price,
        })

        signed = self.account.sign_transaction(txn)
        tx_hash = await self.w3.eth.send_raw_transaction(signed.rawTransaction)
        logger.info(f"Swap tx sent: {tx_hash.hex()}")
        receipt = await self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 1:
            logger.info("Swap successful")
            return tx_hash.hex()
        else:
            logger.error(f"Swap failed: {receipt}")
            raise Exception("Swap transaction failed")
EOF

pip install --upgrade eth-typing eth-utils web3
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
cat << 'EOF' > requirements.txt
Web3==6.11.1
aiohttp==3.9.0
python-dotenv==1.0.0
eth-typing>=4.0.0
eth-utils>=3.0.0
loguru==0.7.2
openai==1.6.1
setuptools>=65.0.0
EOF

pip install --upgrade -r requirements.txt
pip install setuptools
python main.py
