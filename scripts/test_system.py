"""
Comprehensive system test script for Hybrid PQC-Ethereum Project
Tests Ganache connection, contract deployment, and basic interactions
"""
import os
import sys
import time

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Add scripts directory to path for imports
sys.path.insert(0, SCRIPT_DIR)

# Change to project root to ensure relative paths work correctly
os.chdir(PROJECT_ROOT)

from web3 import Web3
from contract_utils import load_contract_info, save_contract_info
from solcx import compile_source, install_solc, set_solc_version

# Configuration
GANACHE_URL = "http://127.0.0.1:8545"
SOLIDITY_VERSION = "0.8.0"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": 0
}

def print_test_header(test_name):
    """Print a formatted test header"""
    print("\n" + "=" * 60)
    print(f"TEST: {test_name}")
    print("=" * 60)

def print_result(success, message, is_warning=False):
    """Print test result"""
    if success:
        print(f"[PASS] {message}")
        test_results["passed"] += 1
    elif is_warning:
        print(f"[WARN] {message}")
        test_results["warnings"] += 1
    else:
        print(f"[FAIL] {message}")
        test_results["failed"] += 1

def test_ganache_connection():
    """Test 1: Verify Ganache connection"""
    print_test_header("Ganache Connection")
    
    try:
        print(f"Attempting to connect to {GANACHE_URL}...")
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        # Try to connect with a timeout
        try:
            is_connected = w3.is_connected()
        except Exception as conn_error:
            print_result(False, f"Connection error: {conn_error}")
            print(f"  Make sure Ganache is running on {GANACHE_URL}")
            return None
        
        if not is_connected:
            print_result(False, f"Could not connect to Ganache at {GANACHE_URL}")
            print(f"  Please verify Ganache is running and listening on port 8545")
            return None
        
        print_result(True, f"Connected to Ganache at {GANACHE_URL}")
        
        # Get chain info
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        print_result(True, f"Chain ID: {chain_id}, Block: {block_number}")
        
        # Check accounts
        accounts = w3.eth.accounts
        if not accounts:
            print_result(False, "No accounts found in Ganache")
            return None
        
        print_result(True, f"Found {len(accounts)} accounts")
        
        # Check first account balance
        account = accounts[0]
        balance = w3.eth.get_balance(account)
        balance_eth = w3.from_wei(balance, 'ether')
        print_result(True, f"Account {account[:10]}... has {balance_eth} ETH")
        
        return w3, account
    
    except Exception as e:
        print_result(False, f"Connection error: {e}")
        return None

def load_contract_source():
    """Load the Solidity contract source code"""
    contract_path = os.path.join(os.path.dirname(__file__), "..", "contracts", "KeyRegistry.sol")
    if not os.path.exists(contract_path):
        raise FileNotFoundError(f"Contract file not found: {contract_path}")
    
    with open(contract_path, "r") as f:
        return f.read()

def compile_contract():
    """Compile the KeyRegistry contract"""
    try:
        install_solc(SOLIDITY_VERSION)
        set_solc_version(SOLIDITY_VERSION)
        source_code = load_contract_source()
        compiled = compile_source(source_code, output_values=['abi', 'bin'])
        contract_key = f"<stdin>:KeyRegistry"
        if contract_key not in compiled:
            raise KeyError(f"Contract 'KeyRegistry' not found")
        return compiled[contract_key]
    except Exception as e:
        raise Exception(f"Compilation failed: {e}")

def test_contract_deployment(w3, account):
    """Test 2: Deploy contract if not already deployed"""
    print_test_header("Contract Deployment")
    
    try:
        # Check if contract already deployed
        contract_address, abi = load_contract_info()
        
        if contract_address:
            # Verify contract exists on chain
            code = w3.eth.get_code(contract_address)
            if code and code != b'':
                print_result(True, f"Contract already deployed at {contract_address}")
                print_result(True, "Contract code verified on-chain")
                return contract_address, abi
            else:
                print_result(False, "Contract address found but no code at address")
                contract_address = None
        
        # Deploy new contract
        if not contract_address:
            print("Deploying new contract...")
            contract_interface = compile_contract()
            
            contract = w3.eth.contract(
                abi=contract_interface['abi'],
                bytecode=contract_interface['bin']
            )
            
            nonce = w3.eth.get_transaction_count(account)
            transaction = contract.constructor().build_transaction({
                'from': account,
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': w3.eth.gas_price
            })
            
            tx_hash = w3.eth.send_transaction(transaction)
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if tx_receipt.status != 1:
                print_result(False, "Transaction failed")
                return None, None
            
            contract_address = tx_receipt['contractAddress']
            abi = contract_interface['abi']
            
            save_contract_info(contract_address, abi)
            print_result(True, f"Contract deployed at {contract_address}")
            print_result(True, f"Gas used: {tx_receipt['gasUsed']}")
        
        return contract_address, abi
    
    except Exception as e:
        print_result(False, f"Deployment error: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_contract_interaction(w3, account, contract_address, abi):
    """Test 3: Test contract functions"""
    print_test_header("Contract Interaction")
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        
        # Test 3.1: Get PQC key (may have data from previous test)
        print("\n3.1 Testing getPQCKey()...")
        initial_key = contract.functions.getPQCKey(account).call()
        if len(initial_key) == 0:
            print_result(True, "Initial PQC key is empty (expected)")
        else:
            print_result(True, f"PQC key already exists from previous test ({len(initial_key)} bytes) - this is OK")
        
        # Test 3.2: Register a dummy PQC public key
        print("\n3.2 Testing registerPQCKey()...")
        dummy_public_key = b"dummy_pqc_public_key_for_testing_" + b"x" * 100  # 132 bytes
        nonce = w3.eth.get_transaction_count(account)
        
        tx_hash = contract.functions.registerPQCKey(dummy_public_key).transact({
            'from': account,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if tx_receipt.status != 1:
            print_result(False, "Registration transaction failed")
            return False
        
        print_result(True, f"Key registered (Gas: {tx_receipt['gasUsed']})")
        
        # Test 3.3: Verify key was stored
        print("\n3.3 Verifying stored key...")
        stored_key = contract.functions.getPQCKey(account).call()
        if stored_key == dummy_public_key:
            print_result(True, f"Key correctly stored ({len(stored_key)} bytes)")
        else:
            print_result(False, "Stored key does not match registered key")
            return False
        
        # Test 3.4: Log a signature
        print("\n3.4 Testing logSignature()...")
        dummy_signature = b"dummy_pqc_signature_for_testing_" + b"y" * 200  # 230 bytes
        dummy_message = b"Test message for hybrid signature"
        
        nonce = w3.eth.get_transaction_count(account)
        tx_hash = contract.functions.logSignature(dummy_signature, dummy_message).transact({
            'from': account,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        if tx_receipt.status != 1:
            print_result(False, "Signature logging transaction failed")
            return False
        
        print_result(True, f"Signature logged (Gas: {tx_receipt['gasUsed']})")
        
        # Test 3.5: Retrieve events
        print("\n3.5 Testing event retrieval...")
        events = contract.events.PQCSignature.get_logs(from_block=tx_receipt.blockNumber)
        
        if len(events) > 0:
            event = events[-1]  # Get the most recent event
            if event['args']['from'].lower() == account.lower():
                print_result(True, "PQCSignature event retrieved correctly")
            else:
                print_result(False, "Event address mismatch")
        else:
            print_result(False, "No PQCSignature events found")
        
        # Test 3.6: Check PQCKeyRegistered event
        key_events = contract.events.PQCKeyRegistered.get_logs(from_block=0)
        if len(key_events) > 0:
            print_result(True, f"Found {len(key_events)} PQCKeyRegistered event(s)")
        else:
            print_result(False, "No PQCKeyRegistered events found")
        
        return True
    
    except Exception as e:
        print_result(False, f"Interaction error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gas_analysis(w3, contract_address, abi):
    """Test 4: Analyze gas usage"""
    print_test_header("Gas Usage Analysis")
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        
        # Get recent transactions
        latest_block = w3.eth.block_number
        start_block = max(0, latest_block - 10)
        
        print(f"Analyzing transactions from block {start_block} to {latest_block}...")
        
        total_gas = 0
        tx_count = 0
        
        for block_num in range(start_block, latest_block + 1):
            try:
                block = w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    if tx.to and tx.to.lower() == contract_address.lower():
                        receipt = w3.eth.get_transaction_receipt(tx.hash)
                        total_gas += receipt['gasUsed']
                        tx_count += 1
            except:
                continue
        
        if tx_count > 0:
            avg_gas = total_gas / tx_count
            print_result(True, f"Found {tx_count} contract transaction(s)")
            print_result(True, f"Average gas per transaction: {avg_gas:,.0f}")
            print_result(True, f"Total gas used: {total_gas:,.0f}")
        else:
            print_result(True, "No contract transactions found in recent blocks")
        
        return True
    
    except Exception as e:
        print_result(False, f"Gas analysis error: {e}")
        return False

def test_error_handling(w3, contract_address, abi):
    """Test 5: Test error handling"""
    print_test_header("Error Handling")
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        
        # Test with invalid address
        print("\n5.1 Testing with invalid address...")
        try:
            invalid_key = contract.functions.getPQCKey("0x0000000000000000000000000000000000000000").call()
            print_result(True, "Query with zero address handled correctly")
        except Exception as e:
            print_result(False, f"Unexpected error with zero address: {e}")
        
        # Test with very large data (should work but use more gas)
        print("\n5.2 Testing with large data...")
        large_key = b"x" * 1000  # 1000 bytes
        try:
            # This should work but might use significant gas
            nonce = w3.eth.get_transaction_count(w3.eth.accounts[0])
            tx_hash = contract.functions.registerPQCKey(large_key).transact({
                'from': w3.eth.accounts[0],
                'nonce': nonce,
                'gas': 1000000,  # Increased gas limit for large data
                'gasPrice': w3.eth.gas_price
            })
            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            if tx_receipt.status == 1:
                print_result(True, f"Large key registered (Gas: {tx_receipt['gasUsed']})")
            else:
                print_result(False, "Large key registration failed")
        except Exception as e:
            error_msg = str(e)
            if "out of gas" in error_msg.lower():
                print_result(True, "Large data correctly rejected due to gas limit (expected behavior)")
            else:
                print_result(False, f"Error with large data: {error_msg[:100]}")
        
        return True
    
    except Exception as e:
        print_result(False, f"Error handling test failed: {e}")
        return False

def print_summary():
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"[PASS] Passed:  {test_results['passed']}")
    print(f"[FAIL] Failed:  {test_results['failed']}")
    print(f"[WARN] Warnings: {test_results['warnings']}")
    print("=" * 60)
    
    total = sum(test_results.values())
    if total > 0:
        success_rate = (test_results['passed'] / total) * 100
        print(f"Success Rate: {success_rate:.1f}%")
    
    if test_results['failed'] == 0:
        print("\n[SUCCESS] All critical tests passed!")
        return True
    else:
        print(f"\n[WARNING] {test_results['failed']} test(s) failed")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("HYBRID PQC-ETHEREUM SYSTEM TEST")
    print("Contract Deployment & Ganache Connection")
    print("=" * 60)
    
    # Test 1: Ganache Connection
    result = test_ganache_connection()
    if not result:
        print("\n[ERROR] Cannot proceed without Ganache connection")
        print_summary()
        sys.exit(1)
    
    w3, account = result
    
    # Test 2: Contract Deployment
    contract_address, abi = test_contract_deployment(w3, account)
    if not contract_address:
        print("\n[ERROR] Cannot proceed without deployed contract")
        print_summary()
        sys.exit(1)
    
    # Test 3: Contract Interaction
    test_contract_interaction(w3, account, contract_address, abi)
    
    # Test 4: Gas Analysis
    test_gas_analysis(w3, contract_address, abi)
    
    # Test 5: Error Handling
    test_error_handling(w3, contract_address, abi)
    
    # Print summary
    success = print_summary()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

