"""
Script to send hybrid-signed transactions (ECDSA + PQC)
"""
import os
import sys

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

import time
from web3 import Web3
from contract_utils import load_contract_info
from key_utils import load_keypair, load_key_info
from register_key import generate_pqc_keypair

# Try to import QuantCrypt
try:
    from quantcrypt import dss
    QUANTCRYPT_AVAILABLE = True
except ImportError:
    print("Warning: quantcrypt not available. Install with: pip install quantcrypt")
    QUANTCRYPT_AVAILABLE = False
    dss = None

# Configuration
GANACHE_URL = "http://127.0.0.1:8545"

def get_algorithm_instance(algorithm_name):
    """
    Get algorithm instance from name
    
    Args:
        algorithm_name: Name of the algorithm
    
    Returns:
        Algorithm instance
    """
    if not QUANTCRYPT_AVAILABLE:
        raise ImportError("QuantCrypt library not available")
    
    # QuantCrypt uses algorithm classes directly
    # NIST ML-DSA (Dilithium)
    if algorithm_name in ["dilithium3", "dilithium65", "mldsa65"]:
        return dss.MLDSA_65()
    elif algorithm_name in ["dilithium2", "dilithium44", "mldsa44"]:
        return dss.MLDSA_44()
    elif algorithm_name in ["dilithium5", "dilithium87", "mldsa87"]:
        return dss.MLDSA_87()
    # NIST SLH-DSA (SPHINCS+)
    elif algorithm_name in ["sphincs", "sphincs128f", "sphincs_small"]:
        return dss.SMALL_SPHINCS()
    elif algorithm_name in ["sphincs192f", "sphincs256f", "sphincs_fast"]:
        return dss.FAST_SPHINCS()
    # NIST FALCON
    elif algorithm_name in ["falcon512", "falcon_512"]:
        return dss.FALCON_512()
    elif algorithm_name in ["falcon1024", "falcon_1024"]:
        return dss.FALCON_1024()
    else:
        raise ValueError(
            f"Unknown algorithm: {algorithm_name}. Supported: "
            "dilithium2/3/5, sphincs128f/fast, falcon512/1024"
        )

def sign_message_pqc(algorithm, private_key, message):
    """
    Sign a message using PQC algorithm
    
    Args:
        algorithm: Algorithm instance or name
        private_key: PQC private key bytes
        message: Message to sign (bytes)
    
    Returns:
        tuple: (signature_bytes, signing_time_seconds)
    """
    print("Signing message with PQC...")
    start_time = time.perf_counter()
    
    try:
        # If algorithm is a string, get the instance
        if isinstance(algorithm, str):
            algorithm = get_algorithm_instance(algorithm)
        
        signature = algorithm.sign(private_key, message)
        sign_time = time.perf_counter() - start_time
        
        print(f"[OK] Message signed in {sign_time:.4f} seconds")
        print(f"     Signature size: {len(signature)} bytes")
        
        return signature, sign_time
    
    except Exception as e:
        print(f"[ERROR] Failed to sign message: {e}")
        raise

def send_hybrid_transaction(w3, account, contract_address, abi, message, pqc_signature):
    """
    Send a transaction that includes PQC signature data
    The transaction itself is signed with ECDSA (implicitly by Web3)
    
    Args:
        w3: Web3 instance
        account: Ethereum account address
        contract_address: Contract address
        abi: Contract ABI
        message: Message that was signed (bytes or str)
        pqc_signature: PQC signature bytes
    
    Returns:
        Transaction receipt
    """
    print("Sending hybrid transaction...")
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        
        # Convert message to bytes if needed
        if isinstance(message, str):
            message_bytes = message.encode('utf-8')
        else:
            message_bytes = message
        
        # Get nonce
        nonce = w3.eth.get_transaction_count(account)
        
        # Estimate gas (with buffer for large signatures)
        estimated_gas = contract.functions.logSignature(pqc_signature, message_bytes).estimate_gas({
            'from': account
        })
        gas_limit = int(estimated_gas * 1.2)  # 20% buffer
        
        # Call logSignature function (ECDSA signs the transaction)
        tx_hash = contract.functions.logSignature(pqc_signature, message_bytes).transact({
            'from': account,
            'nonce': nonce,
            'gas': gas_limit,
            'gasPrice': w3.eth.gas_price
        })
        
        print(f"Transaction sent: {tx_hash.hex()}")
        print("Waiting for confirmation...")
        
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if tx_receipt.status != 1:
            raise Exception("Transaction failed")
        
        print(f"[OK] Hybrid transaction confirmed!")
        print(f"     Transaction hash: {tx_hash.hex()}")
        print(f"     Gas used: {tx_receipt['gasUsed']:,}")
        print(f"     Block: {tx_receipt['blockNumber']}")
        
        return tx_receipt
    
    except Exception as e:
        print(f"[ERROR] Failed to send transaction: {e}")
        raise

def main():
    """Main function for sending hybrid transactions"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Send hybrid-signed transaction (ECDSA + PQC)")
    parser.add_argument(
        "--message",
        type=str,
        default="Hello, hybrid signature world!",
        help="Message to sign and send (default: 'Hello, hybrid signature world!')"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default=None,
        help="PQC algorithm to use (default: auto-detect from registered key)"
    )
    parser.add_argument(
        "--account-index",
        type=int,
        default=0,
        help="Account index to use from Ganache (default: 0)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Hybrid Transaction Sender (ECDSA + PQC)")
    print("=" * 60)
    print()
    
    try:
        # Connect to Ganache
        print(f"Connecting to Ganache at {GANACHE_URL}...")
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        if not w3.is_connected():
            print("[ERROR] Could not connect to Ganache")
            sys.exit(1)
        
        print("[OK] Connected to Ganache")
        
        # Get account
        accounts = w3.eth.accounts
        if args.account_index >= len(accounts):
            print(f"[ERROR] Account index {args.account_index} not available")
            sys.exit(1)
        
        account = accounts[args.account_index]
        print(f"[OK] Using account: {account}")
        print()
        
        # Load contract
        contract_address, abi = load_contract_info()
        if not contract_address:
            print("[ERROR] Contract not deployed. Run 'python scripts/deploy.py' first")
            sys.exit(1)
        
        print(f"[OK] Contract address: {contract_address}")
        print()
        
        # Determine algorithm
        if args.algorithm:
            algorithm_name = args.algorithm
        else:
            # Try to detect from registered keys
            key_info = load_key_info(account)
            if key_info:
                algorithm_name = list(key_info.keys())[0]  # Use first available
                print(f"[INFO] Auto-detected algorithm: {algorithm_name}")
            else:
                print("[ERROR] No registered key found. Please register a key first:")
                print("        python scripts/register_key.py")
                sys.exit(1)
        
        # Load keypair
        print("-" * 60)
        print(f"Loading {algorithm_name} keypair...")
        public_key, private_key = load_keypair(account, algorithm_name)
        
        if private_key is None:
            print(f"[ERROR] Keypair not found for {algorithm_name}")
            print("        Please register a key first:")
            print(f"        python scripts/register_key.py --algorithm {algorithm_name} --save-keys")
            sys.exit(1)
        
        print(f"[OK] Keypair loaded")
        print(f"     Public key size: {len(public_key)} bytes")
        print()
        
        # Get algorithm instance
        algorithm = get_algorithm_instance(algorithm_name)
        
        # Sign message with PQC
        print("-" * 60)
        print(f"Message: {args.message}")
        message_bytes = args.message.encode('utf-8')
        pqc_signature, sign_time = sign_message_pqc(algorithm, private_key, message_bytes)
        print()
        
        # Send hybrid transaction
        print("-" * 60)
        tx_receipt = send_hybrid_transaction(w3, account, contract_address, abi, args.message, pqc_signature)
        print()
        
        print("=" * 60)
        print("[SUCCESS] Hybrid transaction sent successfully!")
        print(f"          PQC signing time: {sign_time:.4f} seconds")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Transaction cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Transaction failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

