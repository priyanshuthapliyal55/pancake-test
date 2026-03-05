const PancakeRouter = artifacts.require("PancakeRouter");

// You need to update these after deploying core contracts
const FACTORY_ADDRESS = process.env.FACTORY_ADDRESS || '0x0000000000000000000000000000000000000000';
const WETH_ADDRESS = '0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9'; // Sepolia WETH

module.exports = async function(deployer, network, accounts) {
  if (FACTORY_ADDRESS === '0x0000000000000000000000000000000000000000') {
    console.error("ERROR: Set FACTORY_ADDRESS environment variable");
    console.error("Example: FACTORY_ADDRESS=0x... truffle migrate --network sepolia");
    return;
  }
  
  console.log("Deploying PancakeRouter...");
  console.log("Factory:", FACTORY_ADDRESS);
  console.log("WETH:", WETH_ADDRESS);
  
  await deployer.deploy(PancakeRouter, FACTORY_ADDRESS, WETH_ADDRESS);
  const router = await PancakeRouter.deployed();
  
  console.log("\n=== Router Deployed ===");
  console.log("Address:", router.address);
  console.log("\nUpdate blockchain.py with:");
  console.log(`Contract.PANCAKE_SMART_ROUTER: '${router.address}'`);
};
