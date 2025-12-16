"""
Script to register PQC public keys on-chain
"""
import os
import sys
import time

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

from web3 import Web3
from contract_utils import load_contract_info

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

def generate_pqc_keypair(algorithm="dilithium3"):
    """
    Generate a PQC key pair using QuantCrypt
    
    Args:
        algorithm: PQC algorithm to use ("dilithium3", "dilithium2", "sphincs")
    
    Returns:
        tuple: (public_key, private_key, algorithm_instance)
    """
    if not QUANTCRYPT_AVAILABLE:
        raise ImportError("QuantCrypt library not available. Install with: pip install quantcrypt")
    
    print(f"Generating {algorithm} key pair...")
    start_time = time.perf_counter()
    
    try:
        # QuantCrypt uses algorithm classes directly with keygen() method
        # NIST ML-DSA (Dilithium) algorithms
        if algorithm == "dilithium3" or algorithm == "dilithium65" or algorithm == "mldsa65":
            alg = dss.MLDSA_65()
        elif algorithm == "dilithium2" or algorithm == "dilithium44" or algorithm == "mldsa44":
            alg = dss.MLDSA_44()
        elif algorithm == "dilithium5" or algorithm == "dilithium87" or algorithm == "mldsa87":
            alg = dss.MLDSA_87()
        # NIST SLH-DSA (SPHINCS+) algorithms
        elif algorithm == "sphincs" or algorithm == "sphincs128f" or algorithm == "sphincs_small":
            alg = dss.SMALL_SPHINCS()
        elif algorithm == "sphincs192f" or algorithm == "sphincs256f" or algorithm == "sphincs_fast":
            alg = dss.FAST_SPHINCS()
        # NIST FALCON algorithms
        elif algorithm == "falcon512" or algorithm == "falcon_512":
            alg = dss.FALCON_512()
        elif algorithm == "falcon1024" or algorithm == "falcon_1024":
            alg = dss.FALCON_1024()
        else:
            raise ValueError(
                f"Unknown algorithm: {algorithm}. Supported: "
                "dilithium2, dilithium3, dilithium5, "
                "sphincs128f, sphincs_fast, "
                "falcon512, falcon1024"
            )
        
        pk, sk = alg.keygen()
        keygen_time = time.perf_counter() - start_time
        
        print(f"[OK] Key pair generated in {keygen_time:.4f} seconds")
        print(f"     Public key size: {len(pk)} bytes")
        print(f"     Private key size: {len(sk)} bytes")
        
        return pk, sk, alg
    
    except Exception as e:
        print(f"[ERROR] Failed to generate key pair: {e}")
        raise

def register_key_on_chain(w3, account, contract_address, abi, public_key):
    """
    Register PQC public key on the KeyRegistry contract
    
    Args:
        w3: Web3 instance
        account: Ethereum account address
        contract_address: Deployed contract address
        abi: Contract ABI
        public_key: PQC public key bytes
    
    Returns:
        Transaction receipt
    """
    print("Registering PQC public key on-chain...")
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        
        # Get current nonce
        nonce = w3.eth.get_transaction_count(account)
        
        # Estimate gas first, then add buffer for large PQC keys
        try:
            estimated_gas = contract.functions.registerPQCKey(public_key).estimate_gas({
                'from': account
            })
            gas_limit = int(estimated_gas * 1.5)  # 50% buffer
        except Exception:
            # If estimation fails, use a large default for PQC keys
            gas_limit = 1000000  # 1M gas should be enough for large keys
        
        # Build and send transaction
        tx_hash = contract.functions.registerPQCKey(public_key).transact({
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
        
        print(f"[OK] Key registered successfully!")
        print(f"     Transaction hash: {tx_hash.hex()}")
        print(f"     Gas used: {tx_receipt['gasUsed']:,}")
        print(f"     Block: {tx_receipt['blockNumber']}")
        
        # Verify registration
        stored_key = contract.functions.getPQCKey(account).call()
        if stored_key == public_key:
            print(f"[OK] Registration verified on-chain")
        else:
            print(f"[WARNING] Stored key doesn't match (length: {len(stored_key)} vs {len(public_key)})")
        
        return tx_receipt
    
    except Exception as e:
        print(f"[ERROR] Failed to register key: {e}")
        raise

def save_keypair_to_file(account, public_key, private_key, algorithm_name):
    """
    Save keypair to file for later use (optional)
    WARNING: In production, never store private keys in plain text!
    """
    from key_utils import save_key_info, get_key_paths
    
    pubkey_file, privkey_file = get_key_paths(account, algorithm_name)
    
    # Save public key (safe to store)
    with open(pubkey_file, "wb") as f:
        f.write(public_key)
    print(f"[INFO] Public key saved to {pubkey_file}")
    
    # Save private key with warning (for testing only!)
    with open(privkey_file, "wb") as f:
        f.write(private_key)
    print(f"[WARNING] Private key saved to {privkey_file} (testing only!)")
    
    # Save key info
    save_key_info(account, algorithm_name, pubkey_file, privkey_file)

def main():
    """Main registration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Register PQC public key on-chain")
    parser.add_argument(
        "--algorithm",
        choices=[
            "dilithium2", "dilithium3", "dilithium5",
            "sphincs128f", "sphincs_fast",
            "falcon512", "falcon1024"
        ],
        default="dilithium3",
        help="PQC algorithm to use (default: dilithium3). "
             "Options: dilithium2/3/5, sphincs128f/fast, falcon512/1024"
    )
    parser.add_argument(
        "--account-index",
        type=int,
        default=0,
        help="Account index to use from Ganache (default: 0)"
    )
    parser.add_argument(
        "--save-keys",
        action="store_true",
        help="Save keypair to file (testing only!)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PQC Key Registration")
    print("=" * 60)
    print(f"Algorithm: {args.algorithm}")
    print()
    
    try:
        # Connect to Ganache
        print(f"Connecting to Ganache at {GANACHE_URL}...")
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        if not w3.is_connected():
            print("[ERROR] Could not connect to Ganache")
            print(f"        Make sure Ganache is running on {GANACHE_URL}")
            sys.exit(1)
        
        print("[OK] Connected to Ganache")
        
        # Get account
        accounts = w3.eth.accounts
        if args.account_index >= len(accounts):
            print(f"[ERROR] Account index {args.account_index} not available")
            print(f"        Available accounts: {len(accounts)}")
            sys.exit(1)
        
        account = accounts[args.account_index]
        balance = w3.eth.get_balance(account)
        balance_eth = w3.from_wei(balance, 'ether')
        print(f"[OK] Using account: {account}")
        print(f"     Balance: {balance_eth} ETH")
        print()
        
        # Load contract address and ABI
        contract_address, abi = load_contract_info()
        if not contract_address:
            print("[ERROR] Contract not deployed. Run 'python scripts/deploy.py' first")
            sys.exit(1)
        
        print(f"[OK] Contract address: {contract_address}")
        print()
        
        # Generate PQC key pair
        print("-" * 60)
        public_key, private_key, algorithm = generate_pqc_keypair(args.algorithm)
        print()
        
        # Register key on-chain
        print("-" * 60)
        tx_receipt = register_key_on_chain(w3, account, contract_address, abi, public_key)
        print()
        
        # Optionally save keys to file
        if args.save_keys:
            print("-" * 60)
            save_keypair_to_file(account, public_key, private_key, args.algorithm)
            print()
        
        print("=" * 60)
        print("[SUCCESS] PQC key registration completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Registration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Registration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

