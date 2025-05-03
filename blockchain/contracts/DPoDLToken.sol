// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title DPoDLToken
 * @dev Basic ERC20 token for the D-PoDL network using AccessControl.
 *      - Grants deployer ADMIN and MINTER roles.
 *      - Only accounts with MINTER_ROLE can mint new tokens.
 */
contract DPoDLToken is ERC20, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    // --- Constructor ---

    /**
     * @dev Sets the token name, symbol, initial supply, and access control roles.
     *      Mints the initial supply to the contract deployer.
     *      Grants deployer DEFAULT_ADMIN_ROLE and MINTER_ROLE.
     * @param initialSupply The total amount of tokens to mint initially.
     */
    constructor(uint256 initialSupply) ERC20("DPoDL Token", "DPDL") {
        // Grant the deployer the default admin role: it will be able to grant and revoke any roles
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        // Grant the deployer the minter role so they can mint if needed or grant it to others
        _grantRole(MINTER_ROLE, msg.sender);

        _mint(msg.sender, initialSupply * (10**decimals())); // Adjust for decimals
    }

    // --- Owner Functions (Now Role-Based) ---

    /**
     * @dev Creates `amount` new tokens and assigns them to `account`.
     *      Can only be called by accounts with MINTER_ROLE. Used for minting block rewards etc.
     * @param account The address that will receive the minted tokens.
     * @param amount The amount of tokens to mint.
     */
    function mint(address account, uint256 amount) public onlyRole(MINTER_ROLE) {
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