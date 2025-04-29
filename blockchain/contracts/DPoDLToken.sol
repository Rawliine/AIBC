// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title DPoDLToken
 * @dev Basic ERC20 token for the D-PoDL network.
 *      - Mints the initial supply to the deployer (owner).
 *      - Owner can mint more tokens (e.g., for block rewards).
 */
contract DPoDLToken is ERC20, Ownable {
    // --- Constructor ---

    /**
     * @dev Sets the token name, symbol, and initial supply.
     *      Mints the initial supply to the contract deployer, who becomes the owner.
     * @param initialSupply The total amount of tokens to mint initially.
     */
    constructor(uint256 initialSupply) ERC20("DPoDL Token", "DPDL") Ownable(msg.sender) {
        _mint(msg.sender, initialSupply * (10**decimals())); // Adjust for decimals
    }

    // --- Owner Functions ---

    /**
     * @dev Creates `amount` new tokens and assigns them to `account`.
     *      Can only be called by the owner. Used for minting block rewards etc.
     * @param account The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address account, uint256 amount) public onlyOwner {
        _mint(account, amount);
    }

    // --- Utility ---

    /**
     * @dev Returns the number of decimals used to get its user representation.
     *      For example, if `decimals` equals `2`, a balance of `505` tokens should
     *      be displayed to a user as `5.05` (`505 / 10 ** 2`).
     *      Tokens usually opt for a value of 18, imitating the relationship between
     *      Ether and Wei. This is the value ERC20 uses by default, unless overridden.
     *      NOTE: This information is only used for _display_ purposes: it in
     *      no way affects any of the arithmetic of the contract.
     */
    // function decimals() public view virtual override returns (uint8) {
    //     return 18; // Default is 18, uncomment to explicitly set if needed
    // }
} 