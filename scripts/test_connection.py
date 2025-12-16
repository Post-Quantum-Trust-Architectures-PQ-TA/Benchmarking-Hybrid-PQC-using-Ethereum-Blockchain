"""
Simple test script to verify Ganache connection
"""
import os
import sys

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web3 import Web3
from contract_utils import load_contract_info

GANACHE_URL = "http://127.0.0.1:8545"

def test_ganache_connection():
    """Test connection to Ganache"""
    print("Testing Ganache connection...")
    try:
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        if not w3.is_connected():
            print(f"❌ Failed to connect to Ganache at {GANACHE_URL}")
            print("   Make sure Ganache is running!")
            return False
        
        print(f"✓ Connected to Ganache at {GANACHE_URL}")
        
        # Get chain ID
        chain_id = w3.eth.chain_id
        print(f"✓ Chain ID: {chain_id}")
        
        # Get accounts
        accounts = w3.eth.accounts
        print(f"✓ Found {len(accounts)} accounts")
        
        if accounts:
            account = accounts[0]
            balance = w3.eth.get_balance(account)
            balance_eth = w3.from_wei(balance, 'ether')
            print(f"✓ First account: {account}")
            print(f"  Balance: {balance_eth} ETH")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_contract_info():
    """Test if contract info exists"""
    print("\nTesting contract info...")
    try:
        contract_address, abi = load_contract_info()
        
        if contract_address is None:
            print("⚠ Contract not deployed yet")
            print("   Run 'python scripts/deploy.py' to deploy the contract")
            return False
        
        print(f"✓ Contract address: {contract_address}")
        print(f"✓ ABI loaded: {len(abi)} functions/events found")
        return True
    
    except Exception as e:
        print(f"❌ Error loading contract info: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Ganache Connection Test")
    print("=" * 50)
    print()
    
    connection_ok = test_ganache_connection()
    contract_ok = test_contract_info()
    
    print("\n" + "=" * 50)
    if connection_ok and contract_ok:
        print("✓ All tests passed!")
    elif connection_ok:
        print("⚠ Ganache connected, but contract not deployed")
    else:
        print("❌ Tests failed - check Ganache connection")
    print("=" * 50)
    
    return connection_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

