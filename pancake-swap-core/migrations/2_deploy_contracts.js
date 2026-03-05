const PancakeFactory = artifacts.require("PancakeFactory");
const WETH9 = artifacts.require("../build/WBNB.sol"); // WBNB is actually WETH9

module.exports = async function(deployer, network, accounts) {
  const deployerAddress = accounts[0];
  
  console.log("Deploying from:", deployerAddress);
  console.log("Network:", network);
  
  // For Sepolia, use existing WETH or deploy new one
  let wethAddress;
  if (network === 'sepolia') {
    // Use existing Sepolia WETH
    wethAddress = '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9';
    console.log("Using existing WETH at:", wethAddress);
  } else {
    // Deploy WETH for other networks
    await deployer.deploy(WETH9);
    const weth = await WETH9.deployed();
    wethAddress = weth.address;
    console.log("WETH deployed at:", wethAddress);
  }
  
  // Deploy Factory
  await deployer.deploy(PancakeFactory, deployerAddress);
  const factory = await PancakeFactory.deployed();
  console.log("PancakeFactory deployed at:", factory.address);
  
  console.log("\n=== Deployment Summary ===");
  console.log("WETH:", wethAddress);
  console.log("Factory:", factory.address);
  console.log("\nNext steps:");
  console.log("1. Deploy PancakeRouter from pancake-swap-periphery");
  console.log("2. Deploy test token (CAKE)");
  console.log("3. Update addresses in rollup-amm-tps-test/blockchain.py");
};
