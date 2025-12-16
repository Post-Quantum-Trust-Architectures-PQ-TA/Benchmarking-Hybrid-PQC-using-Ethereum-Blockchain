"""
Deploy script for KeyRegistry contract
"""
import os
import sys

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web3 import Web3
from solcx import compile_source, install_solc, set_solc_version
from contract_utils import save_contract_info

# Configuration
GANACHE_URL = "http://127.0.0.1:8545"
SOLIDITY_VERSION = "0.8.0"

def load_contract_source():
    """Load the Solidity contract source code"""
    contract_path = os.path.join(os.path.dirname(__file__), "..", "contracts", "KeyRegistry.sol")
    if not os.path.exists(contract_path):
        raise FileNotFoundError(f"Contract file not found: {contract_path}")
    
    with open(contract_path, "r") as f:
        return f.read()

def compile_contract():
    """Compile the KeyRegistry contract"""
    print("Compiling contract...")
    
    try:
        # Install and set Solidity compiler version
        print(f"Installing Solidity compiler version {SOLIDITY_VERSION}...")
        install_solc(SOLIDITY_VERSION)
        set_solc_version(SOLIDITY_VERSION)
        
        # Load and compile contract source
        source_code = load_contract_source()
        print("Compiling Solidity source...")
        compiled = compile_source(source_code, output_values=['abi', 'bin'])
        
        # Extract contract interface
        contract_key = f"<stdin>:KeyRegistry"
        if contract_key not in compiled:
            raise KeyError(f"Contract 'KeyRegistry' not found in compiled output. Available: {list(compiled.keys())}")
        
        contract_interface = compiled[contract_key]
        print("[OK] Contract compiled successfully")
        
        return contract_interface
    
    except Exception as e:
        print(f"Error compiling contract: {e}")
        raise

def deploy_contract(w3, account):
    """Deploy the contract to Ganache"""
    print("Deploying contract to Ganache...")
    
    try:
        # Compile contract
        contract_interface = compile_contract()
        
        # Create contract instance
        contract = w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Get account nonce
        nonce = w3.eth.get_transaction_count(account)
        
        # Build transaction
        transaction = contract.constructor().build_transaction({
            'from': account,
            'nonce': nonce,
            'gas': 2000000,  # Sufficient gas for deployment
            'gasPrice': w3.eth.gas_price
        })
        
        # Sign and send transaction
        print("Sending deployment transaction...")
        tx_hash = w3.eth.send_transaction(transaction)
        
        # Wait for transaction receipt
        print("Waiting for transaction confirmation...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if tx_receipt.status != 1:
            raise Exception("Transaction failed")
        
        contract_address = tx_receipt['contractAddress']
        print(f"[OK] Contract deployed successfully!")
        print(f"  Address: {contract_address}")
        print(f"  Transaction hash: {tx_hash.hex()}")
        print(f"  Gas used: {tx_receipt['gasUsed']}")
        
        return contract_address, contract_interface['abi']
    
    except Exception as e:
        print(f"Error deploying contract: {e}")
        raise

def main():
    """Main deployment function"""
    print("=" * 50)
    print("KeyRegistry Contract Deployment")
    print("=" * 50)
    
    try:
        # Connect to Ganache
        print(f"\nConnecting to Ganache at {GANACHE_URL}...")
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        if not w3.is_connected():
            print(f"Error: Could not connect to Ganache. Make sure it's running on {GANACHE_URL}")
            sys.exit(1)
        
        print("[OK] Connected to Ganache")
        
        # Get first account from Ganache
        accounts = w3.eth.accounts
        if not accounts:
            print("Error: No accounts found in Ganache")
            sys.exit(1)
        
        account = accounts[0]
        balance = w3.eth.get_balance(account)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"[OK] Using account: {account}")
        print(f"  Balance: {balance_eth} ETH")
        
        # Deploy contract
        print("\n" + "-" * 50)
        contract_address, abi = deploy_contract(w3, account)
        
        # Save contract address and ABI to file for other scripts
        print("\n" + "-" * 50)
        save_contract_info(contract_address, abi)
        
        print("\n" + "=" * 50)
        print("Deployment completed successfully!")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\nDeployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nDeployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

