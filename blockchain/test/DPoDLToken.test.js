const { expect } = require("chai");
const { ethers } = require("hardhat");
const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

// Use BigNumber for large numbers - REMOVED for ethers v6
// const { BigNumber } = ethers;

// Helper function to convert token amounts to the smallest unit (considering 18 decimals)
// Returns a value compatible with BigInt
const toWei = (value) => ethers.parseEther(value.toString()); // Use parseEther in v6

// Helper function to convert token amounts from the smallest unit
const fromWei = (value) => ethers.formatEther(typeof value === "string" ? value : value.toString());

describe("DPoDLToken", function () {
  let DPoDLToken;
  let token;
  let owner;
  let addr1;
  let addr2;
  let addrs;
  const initialSupply = 1000000n; // Use BigInt literal for initial supply

  // Before each test, deploy a new instance of the contract
  beforeEach(async function () {
    // Get the ContractFactory and Signers here.
    DPoDLToken = await ethers.getContractFactory("DPoDLToken");
    [owner, addr1, addr2, ...addrs] = await ethers.getSigners();

    // Deploy the contract with the initial supply (pass BigInt)
    token = await DPoDLToken.deploy(initialSupply);
    await token.waitForDeployment(); 
    
  });

  // Define the fixture
  async function deployTokenFixture() {
    const [owner, otherAccount, anotherAccount] = await ethers.getSigners();
    const initialSupply = 1000000n; // Example initial supply

    const DPoDLToken = await ethers.getContractFactory("DPoDLToken");
    const token = await DPoDLToken.deploy(initialSupply);
    await token.waitForDeployment();

    // Return values needed for tests
    return { token, owner, otherAccount, anotherAccount, initialSupply };
  }

  // Test suite for Deployment
  describe("Deployment", function () {
    it("Should set the right owner (admin role)", async function () {
      const { token, owner } = await loadFixture(deployTokenFixture);
      // Check if the owner has the DEFAULT_ADMIN_ROLE
      const DEFAULT_ADMIN_ROLE = await token.DEFAULT_ADMIN_ROLE();
      expect(await token.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.equal(true);
    });

    it("Should assign the total supply of tokens to the owner", async function () {
      const ownerBalance = await token.balanceOf(owner.address);
      const expectedSupply = toWei(initialSupply); // Use helper which returns BigInt compatible value
      expect(await token.totalSupply()).to.equal(expectedSupply);
      expect(ownerBalance).to.equal(expectedSupply);
    });

    it("Should set the correct name and symbol", async function () {
      expect(await token.name()).to.equal("DPoDL Token");
      expect(await token.symbol()).to.equal("DPDL");
    });

     it("Should have 18 decimals", async function () {
      // Decimals returns uint8, directly comparable
      expect(await token.decimals()).to.equal(18);
    });
  });

  // Test suite for Transactions
  describe("Transactions", function () {
    it("Should transfer tokens between accounts", async function () {
      const transferAmount = 50n; // Use BigInt
      // Transfer 50 tokens from owner to addr1
      await token.transfer(addr1.address, toWei(transferAmount));
      const addr1Balance = await token.balanceOf(addr1.address);
      expect(addr1Balance).to.equal(toWei(transferAmount));

      // Transfer 50 tokens from addr1 to addr2
      await token.connect(addr1).transfer(addr2.address, toWei(transferAmount));
      const addr2Balance = await token.balanceOf(addr2.address);
      expect(addr2Balance).to.equal(toWei(transferAmount));

      // Check owner's final balance
      const ownerBalance = await token.balanceOf(owner.address);
      expect(ownerBalance).to.equal(toWei(initialSupply - transferAmount)); 
    });

    it("Should fail if sender doesn't have enough tokens", async function () {
      const initialOwnerBalance = await token.balanceOf(owner.address);
      const transferAmount = 1n; // Use BigInt

      // Try to send 1 token from addr1 (0 tokens) to owner 
      await expect(
        token.connect(addr1).transfer(owner.address, toWei(transferAmount))
      ).to.be.revertedWithCustomError(token, "ERC20InsufficientBalance");

      // Owner balance shouldn't have changed.
      expect(await token.balanceOf(owner.address)).to.equal(initialOwnerBalance);
    });

    it("Should update balances after transfers", async function () {
      const transfer1Amount = 100n; // Use BigInt
      const transfer2Amount = 50n;  // Use BigInt
      const totalTransferred = transfer1Amount + transfer2Amount;

      // Transfer 100 tokens from owner to addr1.
      await token.transfer(addr1.address, toWei(transfer1Amount));

      // Transfer another 50 tokens from owner to addr2.
      await token.transfer(addr2.address, toWei(transfer2Amount));

      // Check balances.
      const finalOwnerBalance = await token.balanceOf(owner.address);
      expect(finalOwnerBalance).to.equal(toWei(initialSupply - totalTransferred));

      const addr1Balance = await token.balanceOf(addr1.address);
      expect(addr1Balance).to.equal(toWei(transfer1Amount));

      const addr2Balance = await token.balanceOf(addr2.address);
      expect(addr2Balance).to.equal(toWei(transfer2Amount));
    });
  });

  // Test suite for Minting (Owner function)
  describe("Minting", function () {
    it("Should allow owner to mint new tokens", async function () {
      const initialTotalSupply = await token.totalSupply();
      const mintAmount = 1000n; // Use BigInt
      
      // Owner mints tokens to addr1
      await token.mint(addr1.address, toWei(mintAmount));

      // Check addr1 balance
      const addr1Balance = await token.balanceOf(addr1.address);
      expect(addr1Balance).to.equal(toWei(mintAmount));

      // Check total supply increase
      const finalTotalSupply = await token.totalSupply();
      // Perform BigInt arithmetic for comparison
      expect(finalTotalSupply).to.equal(BigInt(initialTotalSupply) + toWei(mintAmount)); 
    });

    it("Should prevent non-admins (without MINTER_ROLE) from minting tokens", async function () {
      const { token, otherAccount } = await loadFixture(deployTokenFixture);
      const amount = toWei(50);
      const MINTER_ROLE = await token.MINTER_ROLE();
      // Expect revert due to missing MINTER_ROLE using the custom error
      // const expectedError = `AccessControl: account ${otherAccount.address.toLowerCase()} is missing role ${MINTER_ROLE}`;
      await expect(token.connect(otherAccount).mint(otherAccount.address, amount))
        .to.be.revertedWithCustomError(token, "AccessControlUnauthorizedAccount")
        .withArgs(otherAccount.address, MINTER_ROLE);
        // .to.be.revertedWith(expectedError);
    });
  });

  // Test suite for Allowances (Standard ERC20)
  describe("Allowances", function () {
    it("Should update allowance after approve", async function () {
      const approveAmount = 100n; // Use BigInt
      await token.approve(addr1.address, toWei(approveAmount));
      const allowance = await token.allowance(owner.address, addr1.address);
      expect(allowance).to.equal(toWei(approveAmount));
    });

    it("Should allow spender to transferFrom based on allowance", async function () {
      const approveAmount = 100n; // Use BigInt
      const transferAmount = 50n; // Use BigInt
      await token.approve(addr1.address, toWei(approveAmount));

      // addr1 (spender) transfers 50 from owner to addr2
      await token.connect(addr1).transferFrom(owner.address, addr2.address, toWei(transferAmount));

      // Check balances
      const ownerBalance = await token.balanceOf(owner.address);
      expect(ownerBalance).to.equal(toWei(initialSupply - transferAmount));
      const addr2Balance = await token.balanceOf(addr2.address);
      expect(addr2Balance).to.equal(toWei(transferAmount));

      // Check remaining allowance
      const remainingAllowance = await token.allowance(owner.address, addr1.address);
      expect(remainingAllowance).to.equal(toWei(approveAmount - transferAmount));
    });

    it("Should fail transferFrom if amount exceeds allowance", async function () {
      const approveAmount = 100n; // Use BigInt
      const transferAmount = 150n; // Use BigInt
      await token.approve(addr1.address, toWei(approveAmount));

      // addr1 tries to transfer 150 (more than allowance)
      await expect(
        token.connect(addr1).transferFrom(owner.address, addr2.address, toWei(transferAmount))
      // ).to.be.revertedWith("ERC20: insufficient allowance"); // Check for v6 error message
      ).to.be.revertedWithCustomError(token, "ERC20InsufficientAllowance");
    });

     it("Should fail transferFrom if amount exceeds balance even with allowance", async function () {
      const highApproveAmount = initialSupply + 1000n; // Use BigInt
      const transferAmount = initialSupply + 1n;      // Use BigInt
      await token.approve(addr1.address, toWei(highApproveAmount));

      // addr1 tries to transfer more than owner's balance
      await expect(
        token.connect(addr1).transferFrom(owner.address, addr2.address, toWei(transferAmount))
      ).to.be.revertedWithCustomError(token, "ERC20InsufficientBalance");
    });
  });
}); 