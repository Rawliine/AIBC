require("@nomicfoundation/hardhat-toolbox");
require("hardhat-deploy");
require("@nomicfoundation/hardhat-verify");
require("dotenv").config();

// --- Environment Variables ---
// Load variables from .env file (make sure it exists and is configured)
const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL || "https://sepolia.infura.io/v3/YOUR_INFURA_ID"; // Example fallback
const PRIVATE_KEY = process.env.PRIVATE_KEY; // Load directly, check later if needed
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "YOUR_ETHERSCAN_API_KEY";

// Check if PRIVATE_KEY looks like a valid hex key before including it
const sepoliaAccounts = PRIVATE_KEY && PRIVATE_KEY.startsWith("0x") && PRIVATE_KEY.length === 66 
    ? [PRIVATE_KEY]
    : []; // Use empty array if key is invalid or missing

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200, // Standard default, can be adjusted
      },
      viaIR: true, // Enable the IR-based compilation pipeline
    },
  },
  defaultNetwork: "hardhat",
  networks: {
    hardhat: {
      chainId: 31337,
    },
    localhost: {
        chainId: 31337,
        url: "http://127.0.0.1:8545/", // Default Hardhat Network node URL
    },
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: sepoliaAccounts, // Use the conditional accounts array
      chainId: 11155111,
    },
  },
  etherscan: {
    apiKey: ETHERSCAN_API_KEY,
  },
  sourcify: {
    enabled: false
  },
  namedAccounts: {
    deployer: {
      default: 0,
      1: 0,
      11155111: 0,
    },
    registryOwner: {
        default: 0,
        11155111: 0,
    },
    mempoolOwner: {
        default: 0,
        11155111: 0,
    }
  },
};
