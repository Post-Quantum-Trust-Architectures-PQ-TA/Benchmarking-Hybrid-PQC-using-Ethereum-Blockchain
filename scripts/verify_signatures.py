"""
Script to verify PQC signatures off-chain and collect metrics
"""
import os
import sys

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

import time
import csv
from web3 import Web3
from contract_utils import load_contract_info
from send_hybrid_tx import get_algorithm_instance

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
RESULTS_FILE = os.path.join(PROJECT_ROOT, "data", "results.csv")

def fetch_signature_events(w3, contract_address, abi, from_block=0):
    """
    Fetch PQCSignature events from the blockchain
    
    Args:
        w3: Web3 instance
        contract_address: Contract address
        abi: Contract ABI
        from_block: Starting block number
    
    Returns:
        List of event entries
    """
    print("Fetching signature events...")
    
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        events = contract.events.PQCSignature.get_logs(from_block=from_block)
        print(f"[OK] Found {len(events)} signature event(s)")
        return events
    except Exception as e:
        print(f"[ERROR] Failed to fetch events: {e}")
        return []

def verify_pqc_signature(algorithm, public_key, message, signature):
    """
    Verify a PQC signature off-chain
    
    Args:
        algorithm: Algorithm instance or name
        public_key: PQC public key bytes
        message: Original message bytes
        signature: PQC signature bytes
    
    Returns:
        tuple: (is_valid, verification_time_seconds)
    """
    print("Verifying PQC signature...")
    start_time = time.perf_counter()
    
    try:
        if not QUANTCRYPT_AVAILABLE:
            raise ImportError("QuantCrypt library not available")
        
        # If algorithm is a string, get the instance
        if isinstance(algorithm, str):
            algorithm = get_algorithm_instance(algorithm)
        
        is_valid = algorithm.verify(public_key, message, signature)
        verify_time = time.perf_counter() - start_time
        
        print(f"     Verification time: {verify_time:.4f} seconds")
        print(f"     Signature valid: {is_valid}")
        
        return is_valid, verify_time
    
    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False, 0.0

def get_public_key(w3, contract_address, abi, user_address):
    """
    Get the registered PQC public key for an address
    
    Args:
        w3: Web3 instance
        contract_address: Contract address
        abi: Contract ABI
        user_address: User's Ethereum address
    
    Returns:
        Public key bytes or None if not found
    """
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        public_key = contract.functions.getPQCKey(user_address).call()
        if len(public_key) == 0:
            return None
        return public_key
    except Exception as e:
        print(f"[ERROR] Failed to get public key: {e}")
        return None

def save_results(results):
    """
    Save experiment results to CSV file
    
    Args:
        results: Dictionary with result data
    """
    fieldnames = [
        'algorithm', 'keygen_time', 'sign_time', 'verify_time',
        'public_key_size', 'signature_size', 'gas_used', 'valid', 'block_number'
    ]
    
    file_exists = os.path.exists(RESULTS_FILE)
    with open(RESULTS_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(results)
    
    print(f"[OK] Results saved to {RESULTS_FILE}")

def main():
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify PQC signatures and collect metrics")
    parser.add_argument(
        "--from-block",
        type=int,
        default=0,
        help="Starting block number to fetch events from (default: 0)"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default=None,
        help="PQC algorithm to use (default: auto-detect)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PQC Signature Verification and Metrics Collection")
    print("=" * 60)
    print()
    
    try:
        if not QUANTCRYPT_AVAILABLE:
            print("[ERROR] QuantCrypt library not available")
            print("        Install with: pip install quantcrypt")
            sys.exit(1)
        
        # Connect to Ganache
        print(f"Connecting to Ganache at {GANACHE_URL}...")
        w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
        
        if not w3.is_connected():
            print("[ERROR] Could not connect to Ganache")
            sys.exit(1)
        
        print("[OK] Connected to Ganache")
        print()
        
        # Load contract
        contract_address, abi = load_contract_info()
        if not contract_address:
            print("[ERROR] Contract not deployed. Run 'python scripts/deploy.py' first")
            sys.exit(1)
        
        print(f"[OK] Contract address: {contract_address}")
        print()
        
        # Fetch events
        print("-" * 60)
        events = fetch_signature_events(w3, contract_address, abi, from_block=args.from_block)
        print()
        
        if len(events) == 0:
            print("[INFO] No signature events found")
            print("       Send some hybrid transactions first:")
            print("       python scripts/send_hybrid_tx.py")
            return
        
        # Verify each signature
        verified_count = 0
        invalid_count = 0
        
        for i, event in enumerate(events, 1):
            print("-" * 60)
            print(f"Verifying signature {i}/{len(events)}")
            print("-" * 60)
            
            user_address = event['args']['from']
            signature = event['args']['signature']
            message = event['args']['message']
            block_number = event['blockNumber']
            
            print(f"User: {user_address}")
            print(f"Block: {block_number}")
            print(f"Message size: {len(message)} bytes")
            print(f"Signature size: {len(signature)} bytes")
            
            # Get public key
            public_key = get_public_key(w3, contract_address, abi, user_address)
            
            if public_key is None:
                print("[WARNING] No public key registered for this address")
                print("          Skipping verification")
                continue
            
            print(f"Public key size: {len(public_key)} bytes")
            
            # Determine algorithm (try to detect from signature/key size or use provided)
            algorithm_name = args.algorithm
            if not algorithm_name:
                # Try to detect from signature size first (more reliable)
                # Dilithium signatures: ~2420B (L2), ~3309B (L3), ~4595B (L5)
                # SPHINCS+ signatures: varies by variant
                # Falcon signatures: ~690B (512), ~1330B (1024)
                if len(signature) > 4500:
                    algorithm_name = "dilithium5"
                elif len(signature) > 3200:
                    algorithm_name = "dilithium3"
                elif len(signature) > 2400:
                    algorithm_name = "dilithium2"
                elif len(signature) > 1500:
                    algorithm_name = "falcon1024"
                elif len(signature) > 600:
                    algorithm_name = "falcon512"
                elif len(public_key) > 1900:
                    algorithm_name = "dilithium3"
                elif len(public_key) > 1300:
                    algorithm_name = "dilithium2"
                elif len(public_key) > 1000:
                    algorithm_name = "sphincs_fast"
                else:
                    algorithm_name = "sphincs128f"
                print(f"[INFO] Auto-detected algorithm: {algorithm_name} (sig={len(signature)}B, pk={len(public_key)}B)")
            
            # Verify
            is_valid, verify_time = verify_pqc_signature(algorithm_name, public_key, message, signature)
            
            if is_valid:
                verified_count += 1
                print("[OK] Signature is valid")
            else:
                invalid_count += 1
                print("[FAIL] Signature is invalid")
            
            # Collect metrics
            results = {
                'algorithm': algorithm_name,
                'keygen_time': '',  # Not available from events
                'sign_time': '',    # Not available from events
                'verify_time': f"{verify_time:.6f}",
                'public_key_size': len(public_key),
                'signature_size': len(signature),
                'gas_used': '',  # Would need to fetch from transaction
                'valid': is_valid,
                'block_number': block_number
            }
            save_results(results)
            print()
        
        # Summary
        print("=" * 60)
        print("Verification Summary")
        print("=" * 60)
        print(f"Total signatures: {len(events)}")
        print(f"Valid: {verified_count}")
        print(f"Invalid: {invalid_count}")
        print(f"Results saved to: {RESULTS_FILE}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n[INFO] Verification cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

