const HDWalletProvider = require('truffle-hdwallet-provider');
const fs = require('fs');

// Read mnemonic from file
let mnemonic = '';
try {
  mnemonic = fs.readFileSync('../rollup-amm-tps-test/mnemonic.txt', 'utf8').trim();
} catch (e) {
  console.error('Error reading mnemonic.txt');
}

module.exports = {
  networks: {
    development: {
      host: "127.0.0.1",
      port: 8545,
      network_id: "*",
    },
    sepolia: {
      provider: () => new HDWalletProvider(
        mnemonic, 
        `https://rpc.sepolia.org`
      ),
      network_id: 11155111,
      gas: 5500000,
      confirmations: 2,
      timeoutBlocks: 200,
      skipDryRun: true
    }
  },
  compilers: {
    solc: {
      version: "0.5.16",
      settings: {
        optimizer: {
          enabled: true,
          runs: 999999
        },
        evmVersion: "istanbul"
      }
    }
  }
};
