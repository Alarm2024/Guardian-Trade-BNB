// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// --- Interfaces ---
interface IUniswapV3Pool {
    function flash(
        address recipient,
        uint256 amount0,
        uint256 amount1,
        bytes calldata data
    ) external;

    function token0() external view returns (address);
    function token1() external view returns (address);
    function fee() external view returns (uint24);
    function flashFee(address token, uint256 amount) external view returns (uint256);
}

interface ISwapRouter {
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params)
        external
        payable
        returns (uint256 amountOut);
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

/**
 * @title FlashArbitrage
 * @dev High-frequency yield arbitrage using Uniswap V3 flash swaps.
 *      Executes dual-DEX arbitrage with strict profitability enforcement.
 */
contract FlashArbitrage {

    // --- State Variables ---
    address public owner;
    ISwapRouter public immutable router;
    bool private _locked;

    // --- Events ---
    event ArbitrageExecuted(
        address indexed pool,
        uint256 borrowed,
        uint256 profit,
        uint256 timestamp
    );
    event ProfitTransferred(address indexed recipient, uint256 amount);

    // --- Modifiers ---
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier noReentrant() {
        require(!_locked, "Reentrant call");
        _locked = true;
        _;
        _locked = false;
    }

    // --- Constructor ---
    constructor(address _router) {
        owner = msg.sender;
        router = ISwapRouter(_router);
    }

    // --- Owner Functions ---
    function setOwner(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Zero address");
        owner = newOwner;
    }

    /**
     * @dev Withdraw any leftover tokens (emergency).
     */
    function withdrawTokens(address token, uint256 amount) external onlyOwner {
        IERC20(token).transfer(owner, amount);
    }

    // --- Core Arbitrage ---
    /**
     * @notice Execute arbitrage using a flash loan from a Uniswap V3 pool.
     * @param pool The Uniswap V3 pool to flash borrow from.
     * @param amount0 Amount of token0 to borrow (0 if not needed).
     * @param amount1 Amount of token1 to borrow (0 if not needed).
     * @param swapPath0to1 Encoded path for swapping token0 -> token1 (via SwapRouter).
     * @param swapPath1to0 Encoded path for swapping token1 -> token0 (via SwapRouter).
     * @param minProfit Minimum net profit in token0 (or token1 if only token1 borrowed).
     * @dev The callback will perform the swaps and revert if not profitable.
     */
    function executeArbitrage(
        address pool,
        uint256 amount0,
        uint256 amount1,
        bytes calldata swapPath0to1,
        bytes calldata swapPath1to0,
        uint256 minProfit
    ) external onlyOwner noReentrant {
        require(amount0 > 0 || amount1 > 0, "No amount to borrow");
        // Encode parameters for callback
        bytes memory data = abi.encode(
            amount0,
            amount1,
            swapPath0to1,
            swapPath1to0,
            minProfit,
            msg.sender // profit receiver
        );
        // Initiate flash loan
        IUniswapV3Pool(pool).flash(address(this), amount0, amount1, data);
    }

    /**
     * @notice Uniswap V3 flash callback.
     * @dev Performs arbitrage swaps, repays loan, and transfers profit.
     */
    struct CallbackVars {
        uint256 borrow0;
        uint256 borrow1;
        bytes path0to1;
        bytes path1to0;
        uint256 minProfit;
        address profitRecipient;
        IUniswapV3Pool pool;
        address token0;
        address token1;
        uint256 repayAmount0;
        uint256 repayAmount1;
    }

    function uniswapV3SwapCallback(
        int256 /*amount0Delta*/,
        int256 /*amount1Delta*/,
        bytes calldata data
    ) external {
        CallbackVars memory v;
        (v.borrow0, v.borrow1, v.path0to1, v.path1to0, v.minProfit, v.profitRecipient) =
            abi.decode(data, (uint256, uint256, bytes, bytes, uint256, address));

        v.pool = IUniswapV3Pool(msg.sender);
        v.token0 = v.pool.token0();
        v.token1 = v.pool.token1();

        require(v.borrow0 > 0 || v.borrow1 > 0, "Nothing borrowed");
        require(!(v.borrow0 > 0 && v.borrow1 > 0), "Only one token borrow supported");

        v.repayAmount0 = v.borrow0 + v.pool.flashFee(v.token0, v.borrow0);
        v.repayAmount1 = v.borrow1 + v.pool.flashFee(v.token1, v.borrow1);

        if (v.borrow0 > 0) {
            _handleBorrowToken0(v);
        } else {
            _handleBorrowToken1(v);
        }
    }

    function _handleBorrowToken0(CallbackVars memory v) internal {
        IERC20(v.token0).approve(address(router), v.borrow0);
        uint256 amountOut1 = router.exactInputSingle(
            ISwapRouter.ExactInputSingleParams({
                tokenIn: v.token0,
                tokenOut: v.token1,
                fee: _decodeFirstFee(v.path0to1),
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: v.borrow0,
                amountOutMinimum: 1,
                sqrtPriceLimitX96: 0
            })
        );

        IERC20(v.token1).approve(address(router), amountOut1);
        uint256 amountOut0 = router.exactInputSingle(
            ISwapRouter.ExactInputSingleParams({
                tokenIn: v.token1,
                tokenOut: v.token0,
                fee: _decodeFirstFee(v.path1to0),
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountOut1,
                amountOutMinimum: v.repayAmount0 + v.minProfit,
                sqrtPriceLimitX96: 0
            })
        );

        require(IERC20(v.token0).balanceOf(address(this)) >= v.repayAmount0, "Insufficient repayment");
        uint256 profit = IERC20(v.token0).balanceOf(address(this)) - v.repayAmount0;
        require(profit >= v.minProfit, "Profit below minimum");

        IERC20(v.token0).transfer(v.profitRecipient, profit);
        emit ProfitTransferred(v.profitRecipient, profit);
        emit ArbitrageExecuted(address(v.pool), v.borrow0, profit, block.timestamp);
    }

    function _handleBorrowToken1(CallbackVars memory v) internal {
        IERC20(v.token1).approve(address(router), v.borrow1);
        uint256 amountOut0 = router.exactInputSingle(
            ISwapRouter.ExactInputSingleParams({
                tokenIn: v.token1,
                tokenOut: v.token0,
                fee: _decodeFirstFee(v.path1to0),
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: v.borrow1,
                amountOutMinimum: 1,
                sqrtPriceLimitX96: 0
            })
        );

        IERC20(v.token0).approve(address(router), amountOut0);
        uint256 amountOut1 = router.exactInputSingle(
            ISwapRouter.ExactInputSingleParams({
                tokenIn: v.token0,
                tokenOut: v.token1,
                fee: _decodeFirstFee(v.path0to1),
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountOut0,
                amountOutMinimum: v.repayAmount1 + v.minProfit,
                sqrtPriceLimitX96: 0
            })
        );

        require(IERC20(v.token1).balanceOf(address(this)) >= v.repayAmount1, "Insufficient repayment");
        uint256 profit = IERC20(v.token1).balanceOf(address(this)) - v.repayAmount1;
        require(profit >= v.minProfit, "Profit below minimum");

        IERC20(v.token1).transfer(v.profitRecipient, profit);
        emit ProfitTransferred(v.profitRecipient, profit);
        emit ArbitrageExecuted(address(v.pool), v.borrow1, profit, block.timestamp);
    }

    // --- Helper: decode fee from path (assumes first fee is at offset 20) ---
    function _decodeFirstFee(bytes memory path) internal pure returns (uint24 fee) {
        // Uniswap V3 path: tokenA (20 bytes) + fee (3 bytes) + tokenB (20 bytes)
        // For a single hop, the fee is at offset 20.
        require(path.length >= 23, "Invalid path length");
        bytes3 feeBytes;
        assembly {
            feeBytes := mload(add(add(path, 0x20), 20))
        }
        fee = uint24(bytes3(feeBytes));
    }

    // --- Allow contract to receive native tokens (if needed) ---
    receive() external payable {}
}
