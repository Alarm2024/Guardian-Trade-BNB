# Guardian Angel Carbon

Guardian Angel Carbon is a sophisticated, high-frequency DeFi arbitrage platform designed for secure and optimized yield generation. By leveraging Uniswap V3 flash swap mechanics, the system executes risk-managed, dual-DEX arbitrage while maintaining strict profitability and safety standards.

## Features

- **Automated Flash Arbitrage**: Executes atomic arbitrage swaps using Uniswap V3 flash loans.
- **Strict Profitability Enforcement**: Built-in slippage protection and minimum profit requirements ensure that no transaction is executed unless it is net-profitable after fees.
- **Robust Security Framework**: Extensive test coverage using Foundry, including fuzz testing and mainnet forking to simulate real-world market conditions.
- **Real-time Monitoring**: Integrated Telegram bot for monitoring market conditions, testing cycles, and execution alerts.

## Getting Started

### Prerequisites

- [Foundry](https://book.getfoundry.sh/getting-started/installation)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd <repository-directory>

# Install dependencies
forge install
```

### Running Tests

To run the full suite of security and integration tests against a mainnet fork, ensure your `MAINNET_RPC_URL` is set:

```bash
export MAINNET_RPC_URL="<your-rpc-url>"
forge test --match-path test/FlashArbitrage.t.sol
```

## Security Disclaimer

**Use of this software involves significant financial risk.**
The `FlashArbitrage` contract operates in a high-stakes, competitive DeFi environment. While we have implemented rigorous security measures, including reentrancy guards, atomic execution checks, and extensive fuzz testing, the risk of smart contract exploits, market volatility, or failed execution remains. 

**This software is provided "as is," without warranty of any kind.** Users are solely responsible for all financial decisions and potential losses. Always audit the code yourself and start with small, non-critical amounts in a controlled environment before deploying to mainnet.
