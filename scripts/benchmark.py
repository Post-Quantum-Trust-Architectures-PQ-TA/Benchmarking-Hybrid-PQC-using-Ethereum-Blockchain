"""
Comprehensive Benchmarking Suite for Research Paper
Runs systematic performance tests with statistical analysis
"""
import os
import sys
import time
import statistics
import json
import csv
from datetime import datetime
from collections import defaultdict

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

from web3 import Web3
from contract_utils import load_contract_info
from register_key import generate_pqc_keypair, register_key_on_chain
from send_hybrid_tx import sign_message_pqc, send_hybrid_transaction, get_algorithm_instance
from verify_signatures import verify_pqc_signature, get_public_key

# Try to import QuantCrypt
try:
    from quantcrypt import dss
    QUANTCRYPT_AVAILABLE = True
except ImportError:
    print("Warning: quantcrypt not available. Install with: pip install quantcrypt")
    QUANTCRYPT_AVAILABLE = False
    dss = None

# Try to import ECDSA libraries
import hashlib
ECDSA_AVAILABLE = False
ECDSA_LIB = None

try:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    ECDSA_AVAILABLE = True
    ECDSA_LIB = 'cryptography'
except ImportError:
    try:
        from ecdsa import SigningKey, SECP256k1
        ECDSA_AVAILABLE = True
        ECDSA_LIB = 'ecdsa'
    except ImportError:
        ECDSA_AVAILABLE = False
        ECDSA_LIB = None
        print("Warning: ECDSA libraries not available. Install with: pip install cryptography or pip install ecdsa")

# Configuration
GANACHE_URL = "http://127.0.0.1:8545"
RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "benchmarks")
BENCHMARK_RESULTS_FILE = os.path.join(RESULTS_DIR, f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

# All available PQC algorithms for research
ALL_ALGORITHMS = [
    "dilithium2",   # ML-DSA-44 (NIST Level 2)
    "dilithium3",   # ML-DSA-65 (NIST Level 3)
    "dilithium5",   # ML-DSA-87 (NIST Level 5)
    "sphincs128f",  # SLH-DSA Small (NIST Level 1)
    "sphincs_fast", # SLH-DSA Fast (NIST Level 3/5)
    "falcon512",    # FALCON-512 (NIST Level 1)
    "falcon1024",   # FALCON-1024 (NIST Level 5)
]

# ECDSA baseline for comparison
INCLUDE_ECDSA = True

def ensure_results_directory():
    """Ensure benchmark results directory exists"""
    os.makedirs(RESULTS_DIR, exist_ok=True)

def benchmark_ecdsa_key_generation(iterations=20):
    """
    Benchmark ECDSA (secp256k1) key generation for baseline comparison
    
    Args:
        iterations: Number of iterations
    
    Returns:
        dict: Benchmark results with statistics
    """
    print(f"  Benchmarking ECDSA (secp256k1) key generation ({iterations} iterations)...")
    
    if not ECDSA_AVAILABLE:
        return None
    
    times = []
    public_key_sizes = []
    private_key_sizes = []
    
    try:
        if ECDSA_LIB == 'cryptography':
            # Using cryptography library
            for i in range(iterations):
                start = time.perf_counter()
                private_key = ec.generate_private_key(ec.SECP256K1(), default_backend())
                public_key = private_key.public_key()
                elapsed = time.perf_counter() - start
                
                times.append(elapsed)
                # ECDSA public key is 65 bytes (uncompressed) or 33 bytes (compressed)
                public_key_sizes.append(65)  # Uncompressed format
                private_key_sizes.append(32)  # Private key is 32 bytes
                
                if (i + 1) % 5 == 0:
                    print(f"    Completed {i + 1}/{iterations} iterations...")
        elif ECDSA_LIB == 'ecdsa':
            # Using ecdsa library
            for i in range(iterations):
                start = time.perf_counter()
                sk = SigningKey.generate(curve=SECP256k1)
                vk = sk.get_verifying_key()
                elapsed = time.perf_counter() - start
                
                times.append(elapsed)
                public_key_sizes.append(64)  # 64 bytes for public key
                private_key_sizes.append(32)  # 32 bytes for private key
                
                if (i + 1) % 5 == 0:
                    print(f"    Completed {i + 1}/{iterations} iterations...")
        else:
            print("    [ERROR] No ECDSA library available")
            return None
    except Exception as e:
        print(f"    [ERROR] ECDSA key generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    if not times:
        return None
    
    return {
        'algorithm': 'ecdsa',
        'operation': 'key_generation',
        'iterations': len(times),
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'public_key_size': public_key_sizes[0] if public_key_sizes else 65,
        'private_key_size': private_key_sizes[0] if private_key_sizes else 32,
        'timestamp': datetime.now().isoformat()
    }

def benchmark_ecdsa_signing(private_key_obj, message, iterations=20):
    """
    Benchmark ECDSA message signing for baseline comparison
    
    Args:
        private_key_obj: ECDSA private key object
        message: Message to sign
        iterations: Number of iterations
    
    Returns:
        dict: Benchmark results with statistics
    """
    print(f"  Benchmarking ECDSA (secp256k1) signing ({iterations} iterations)...")
    
    if not ECDSA_AVAILABLE:
        return None
    
    times = []
    signature_sizes = []
    
    try:
        if ECDSA_LIB == 'cryptography':
            # Using cryptography library
            for i in range(iterations):
                start = time.perf_counter()
                signature = private_key_obj.sign(message, ec.ECDSA(hashes.SHA256()))
                elapsed = time.perf_counter() - start
                
                times.append(elapsed)
                signature_sizes.append(len(signature))  # ECDSA signature is typically 64-72 bytes
                
                if (i + 1) % 5 == 0:
                    print(f"    Completed {i + 1}/{iterations} iterations...")
        elif ECDSA_LIB == 'ecdsa':
            # Using ecdsa library
            for i in range(iterations):
                start = time.perf_counter()
                signature = private_key_obj.sign(message, hashfunc=hashlib.sha256)
                elapsed = time.perf_counter() - start
                
                times.append(elapsed)
                signature_sizes.append(len(signature))  # ECDSA signature is 64 bytes
                
                if (i + 1) % 5 == 0:
                    print(f"    Completed {i + 1}/{iterations} iterations...")
        else:
            print("    [ERROR] No ECDSA library available")
            return None
    except Exception as e:
        print(f"    [ERROR] ECDSA signing failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    if not times:
        return None
    
    return {
        'algorithm': 'ecdsa',
        'operation': 'signing',
        'iterations': len(times),
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'signature_size': signature_sizes[0] if signature_sizes else 64,
        'message_size': len(message),
        'timestamp': datetime.now().isoformat()
    }

def benchmark_ecdsa_verification(public_key_obj, message, signature, iterations=20):
    """
    Benchmark ECDSA signature verification for baseline comparison
    
    Args:
        public_key_obj: ECDSA public key object
        message: Original message
        signature: Signature bytes
        iterations: Number of iterations
    
    Returns:
        dict: Benchmark results with statistics
    """
    print(f"  Benchmarking ECDSA (secp256k1) verification ({iterations} iterations)...")
    
    if not ECDSA_AVAILABLE:
        return None
    
    times = []
    
    try:
        if ECDSA_LIB == 'cryptography':
            # Using cryptography library
            for i in range(iterations):
                start = time.perf_counter()
                try:
                    public_key_obj.verify(signature, message, ec.ECDSA(hashes.SHA256()))
                    is_valid = True
                except:
                    is_valid = False
                elapsed = time.perf_counter() - start
                
                if is_valid:
                    times.append(elapsed)
                
                if (i + 1) % 5 == 0:
                    print(f"    Completed {i + 1}/{iterations} iterations...")
        elif ECDSA_LIB == 'ecdsa':
            # Using ecdsa library
            for i in range(iterations):
                start = time.perf_counter()
                try:
                    public_key_obj.verify(signature, message, hashfunc=hashlib.sha256)
                    is_valid = True
                except:
                    is_valid = False
                elapsed = time.perf_counter() - start
                
                if is_valid:
                    times.append(elapsed)
                
                if (i + 1) % 5 == 0:
                    print(f"    Completed {i + 1}/{iterations} iterations...")
        else:
            print("    [ERROR] No ECDSA library available")
            return None
    except Exception as e:
        print(f"    [ERROR] ECDSA verification failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    if not times:
        return None
    
    return {
        'algorithm': 'ecdsa',
        'operation': 'verification',
        'iterations': len(times),
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'timestamp': datetime.now().isoformat()
    }

def benchmark_ecdsa(iterations=20):
    """
    Complete ECDSA benchmark for baseline comparison
    
    Args:
        iterations: Number of iterations per operation
    
    Returns:
        dict: Complete ECDSA benchmark results
    """
    print(f"\n{'='*70}")
    print(f"Benchmarking: ECDSA (secp256k1) - BASELINE")
    print(f"{'='*70}")
    
    results = {
        'algorithm': 'ecdsa',
        'timestamp': datetime.now().isoformat(),
        'iterations': iterations
    }
    
    # 1. Key Generation
    keygen_result = benchmark_ecdsa_key_generation(iterations)
    if keygen_result:
        results['key_generation'] = keygen_result
        
        # Generate keys for subsequent tests
        try:
            if ECDSA_LIB == 'cryptography':
                private_key_obj = ec.generate_private_key(ec.SECP256K1(), default_backend())
                public_key_obj = private_key_obj.public_key()
            elif ECDSA_LIB == 'ecdsa':
                private_key_obj = SigningKey.generate(curve=SECP256k1)
                public_key_obj = private_key_obj.get_verifying_key()
            else:
                print("  [ERROR] No ECDSA library available")
                return None
        except Exception as e:
            print(f"  [ERROR] Failed to generate ECDSA keys: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print(f"  [SKIP] ECDSA key generation benchmark failed")
        return None
    
    # 2. Signing
    test_message = b"Benchmark test message for research paper analysis" + b"x" * 100
    signing_result = benchmark_ecdsa_signing(private_key_obj, test_message, iterations)
    if signing_result:
        results['signing'] = signing_result
        
        # Get signature for verification test
        try:
            if ECDSA_LIB == 'cryptography':
                signature = private_key_obj.sign(test_message, ec.ECDSA(hashes.SHA256()))
            elif ECDSA_LIB == 'ecdsa':
                signature = private_key_obj.sign(test_message, hashfunc=hashlib.sha256)
            else:
                signature = None
        except Exception as e:
            print(f"  [ERROR] Failed to generate ECDSA signature: {e}")
            signature = None
    else:
        print(f"  [SKIP] ECDSA signing benchmark failed")
        signature = None
    
    # 3. Verification
    if public_key_obj and signature:
        verification_result = benchmark_ecdsa_verification(
            public_key_obj, test_message, signature, iterations
        )
        if verification_result:
            results['verification'] = verification_result
    else:
        print(f"  [SKIP] ECDSA verification benchmark skipped")
    
    return results

def benchmark_key_generation(algorithm, iterations=20):
    """
    Benchmark PQC key generation with statistical analysis
    
    Args:
        algorithm: Algorithm name
        iterations: Number of iterations
    
    Returns:
        dict: Benchmark results with statistics
    """
    print(f"  Benchmarking {algorithm} key generation ({iterations} iterations)...")
    
    if not QUANTCRYPT_AVAILABLE:
        return None
    
    times = []
    public_key_sizes = []
    private_key_sizes = []
    
    for i in range(iterations):
        try:
            start = time.perf_counter()
            pk, sk, alg = generate_pqc_keypair(algorithm)
            elapsed = time.perf_counter() - start
            
            times.append(elapsed)
            public_key_sizes.append(len(pk))
            private_key_sizes.append(len(sk))
            
            if (i + 1) % 5 == 0:
                print(f"    Completed {i + 1}/{iterations} iterations...")
        
        except Exception as e:
            print(f"    [ERROR] Iteration {i + 1} failed: {e}")
            continue
    
    if not times:
        return None
    
    return {
        'algorithm': algorithm,
        'operation': 'key_generation',
        'iterations': len(times),
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'public_key_size': public_key_sizes[0] if public_key_sizes else 0,
        'private_key_size': private_key_sizes[0] if private_key_sizes else 0,
        'timestamp': datetime.now().isoformat()
    }

def benchmark_signing(algorithm, private_key, message, iterations=20):
    """
    Benchmark PQC message signing with statistical analysis
    
    Args:
        algorithm: Algorithm name
        private_key: Private key bytes
        message: Message to sign
        iterations: Number of iterations
    
    Returns:
        dict: Benchmark results with statistics
    """
    print(f"  Benchmarking {algorithm} signing ({iterations} iterations)...")
    
    if not QUANTCRYPT_AVAILABLE:
        return None
    
    alg = get_algorithm_instance(algorithm)
    times = []
    signature_sizes = []
    
    for i in range(iterations):
        try:
            sig, sign_time = sign_message_pqc(alg, private_key, message)
            times.append(sign_time)
            signature_sizes.append(len(sig))
            
            if (i + 1) % 5 == 0:
                print(f"    Completed {i + 1}/{iterations} iterations...")
        
        except Exception as e:
            print(f"    [ERROR] Iteration {i + 1} failed: {e}")
            continue
    
    if not times:
        return None
    
    return {
        'algorithm': algorithm,
        'operation': 'signing',
        'iterations': len(times),
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'signature_size': signature_sizes[0] if signature_sizes else 0,
        'message_size': len(message),
        'timestamp': datetime.now().isoformat()
    }

def benchmark_verification(algorithm, public_key, message, signature, iterations=20):
    """
    Benchmark PQC signature verification with statistical analysis
    
    Args:
        algorithm: Algorithm name
        public_key: Public key bytes
        message: Original message
        signature: Signature bytes
        iterations: Number of iterations
    
    Returns:
        dict: Benchmark results with statistics
    """
    print(f"  Benchmarking {algorithm} verification ({iterations} iterations)...")
    
    if not QUANTCRYPT_AVAILABLE:
        return None
    
    times = []
    
    for i in range(iterations):
        try:
            is_valid, verify_time = verify_pqc_signature(algorithm, public_key, message, signature)
            if is_valid:
                times.append(verify_time)
            else:
                print(f"    [WARNING] Iteration {i + 1}: Invalid signature")
            
            if (i + 1) % 5 == 0:
                print(f"    Completed {i + 1}/{iterations} iterations...")
        
        except Exception as e:
            print(f"    [ERROR] Iteration {i + 1} failed: {e}")
            continue
    
    if not times:
        return None
    
    return {
        'algorithm': algorithm,
        'operation': 'verification',
        'iterations': len(times),
        'times': times,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times),
        'max': max(times),
        'timestamp': datetime.now().isoformat()
    }

def benchmark_gas_usage(w3, account, contract_address, abi, algorithm, public_key, message, signature):
    """
    Benchmark gas usage for blockchain operations
    
    Returns:
        dict: Gas usage metrics
    """
    print(f"  Benchmarking {algorithm} gas usage...")
    
    try:
        # Register key (if not already registered)
        contract = w3.eth.contract(address=contract_address, abi=abi)
        stored_key = contract.functions.getPQCKey(account).call()
        
        if len(stored_key) == 0 or stored_key != public_key:
            # Register key
            tx_receipt = register_key_on_chain(w3, account, contract_address, abi, public_key)
            registration_gas = tx_receipt['gasUsed'] if tx_receipt else 0
        else:
            registration_gas = 0  # Already registered
        
        # Send hybrid transaction
        tx_receipt = send_hybrid_transaction(w3, account, contract_address, abi, message, signature)
        transaction_gas = tx_receipt['gasUsed'] if tx_receipt else 0
        
        return {
            'algorithm': algorithm,
            'operation': 'gas_usage',
            'registration_gas': registration_gas,
            'transaction_gas': transaction_gas,
            'total_gas': registration_gas + transaction_gas,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"    [ERROR] Gas benchmarking failed: {e}")
        return None

def benchmark_algorithm(algorithm, iterations=20, test_gas=True):
    """
    Complete benchmark for one algorithm
    
    Args:
        algorithm: Algorithm name
        iterations: Number of iterations per operation
        test_gas: Whether to test gas usage
    
    Returns:
        dict: Complete benchmark results
    """
    print(f"\n{'='*70}")
    print(f"Benchmarking: {algorithm.upper()}")
    print(f"{'='*70}")
    
    results = {
        'algorithm': algorithm,
        'timestamp': datetime.now().isoformat(),
        'iterations': iterations
    }
    
    # 1. Key Generation
    keygen_result = benchmark_key_generation(algorithm, iterations)
    if keygen_result:
        results['key_generation'] = keygen_result
        public_key = None
        private_key = None
        
        # Generate keys for subsequent tests
        try:
            public_key, private_key, alg_instance = generate_pqc_keypair(algorithm)
        except:
            pass
    else:
        print(f"  [SKIP] Key generation benchmark failed for {algorithm}")
        return None
    
    # 2. Signing
    if private_key:
        test_message = b"Benchmark test message for research paper analysis" + b"x" * 100
        signing_result = benchmark_signing(algorithm, private_key, test_message, iterations)
        if signing_result:
            results['signing'] = signing_result
            signature = None
            
            # Get signature for verification test
            try:
                alg = get_algorithm_instance(algorithm)
                signature, _ = sign_message_pqc(alg, private_key, test_message)
            except:
                pass
        else:
            print(f"  [SKIP] Signing benchmark failed for {algorithm}")
    else:
        print(f"  [SKIP] Signing benchmark skipped (no private key)")
        signature = None
    
    # 3. Verification
    if public_key and signature:
        verification_result = benchmark_verification(
            algorithm, public_key, test_message, signature, iterations
        )
        if verification_result:
            results['verification'] = verification_result
    else:
        print(f"  [SKIP] Verification benchmark skipped")
    
    # 4. Gas Usage (optional, requires blockchain)
    if test_gas and public_key and signature:
        try:
            w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
            if w3.is_connected():
                contract_address, abi = load_contract_info()
                if contract_address:
                    account = w3.eth.accounts[0]
                    gas_result = benchmark_gas_usage(
                        w3, account, contract_address, abi, algorithm,
                        public_key, test_message, signature
                    )
                    if gas_result:
                        results['gas_usage'] = gas_result
        except Exception as e:
            print(f"  [SKIP] Gas benchmarking skipped: {e}")
    
    return results

def save_benchmark_results(all_results):
    """
    Save benchmark results to JSON file
    
    Args:
        all_results: List of benchmark results
    """
    ensure_results_directory()
    
    output = {
        'benchmark_date': datetime.now().isoformat(),
        'total_algorithms': len(all_results),
        'results': all_results
    }
    
    with open(BENCHMARK_RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[OK] Benchmark results saved to: {BENCHMARK_RESULTS_FILE}")
    return BENCHMARK_RESULTS_FILE

def generate_comparison_table(all_results):
    """
    Generate algorithm comparison table for research paper
    
    Args:
        all_results: List of benchmark results
    
    Returns:
        str: Formatted comparison table
    """
    print("\n" + "="*70)
    print("ALGORITHM COMPARISON TABLE")
    print("="*70)
    
    table = []
    table.append(f"{'Algorithm':<15} {'Keygen (ms)':<15} {'Sign (ms)':<15} {'Verify (ms)':<15} {'PubKey (B)':<12} {'Sig (B)':<12}")
    table.append("-" * 90)
    
    for result in all_results:
        algo = result.get('algorithm', 'unknown')
        keygen = result.get('key_generation', {})
        signing = result.get('signing', {})
        verify = result.get('verification', {})
        
        keygen_mean = keygen.get('mean', 0) * 1000 if keygen else 0
        sign_mean = signing.get('mean', 0) * 1000 if signing else 0
        verify_mean = verify.get('mean', 0) * 1000 if verify else 0
        pubkey_size = keygen.get('public_key_size', 0) if keygen else 0
        sig_size = signing.get('signature_size', 0) if signing else 0
        
        table.append(
            f"{algo:<15} {keygen_mean:>12.2f} {sign_mean:>12.2f} {verify_mean:>12.2f} "
            f"{pubkey_size:>10} {sig_size:>10}"
        )
    
    table_str = "\n".join(table)
    print(table_str)
    
    # Save to file
    comparison_file = os.path.join(RESULTS_DIR, "comparison_table.txt")
    with open(comparison_file, 'w') as f:
        f.write(table_str)
    
    print(f"\n[OK] Comparison table saved to: {comparison_file}")
    return table_str

def main():
    """Main benchmarking function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive PQC Benchmarking Suite for Research Paper"
    )
    parser.add_argument(
        "--algorithms",
        nargs="+",
        default=ALL_ALGORITHMS,
        help=f"Algorithms to benchmark (default: all). Available: {', '.join(ALL_ALGORITHMS)}"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=20,
        help="Number of iterations per operation (default: 20)"
    )
    parser.add_argument(
        "--skip-gas",
        action="store_true",
        help="Skip gas usage benchmarking"
    )
    parser.add_argument(
        "--skip-ecdsa",
        action="store_true",
        help="Skip ECDSA baseline benchmarking"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    print("="*70)
    print("  COMPREHENSIVE PQC BENCHMARKING SUITE")
    print("  For Research Paper Publication")
    print("="*70)
    print(f"\nAlgorithms to benchmark: {', '.join(args.algorithms)}")
    print(f"Iterations per operation: {args.iterations}")
    print(f"Skip gas benchmarking: {args.skip_gas}")
    print(f"Include ECDSA baseline: {not args.skip_ecdsa}")
    print()
    
    if not QUANTCRYPT_AVAILABLE:
        print("[ERROR] QuantCrypt library not available")
        print("        Install with: pip install quantcrypt")
        sys.exit(1)
    
    all_results = []
    
    # Benchmark ECDSA baseline first (if requested)
    if not args.skip_ecdsa and INCLUDE_ECDSA:
        if ECDSA_AVAILABLE:
            try:
                ecdsa_result = benchmark_ecdsa(args.iterations)
                if ecdsa_result:
                    all_results.append(ecdsa_result)
            except Exception as e:
                print(f"[WARNING] ECDSA benchmarking failed: {e}")
                print("          Continuing with PQC algorithms only...")
        else:
            print("[WARNING] ECDSA libraries not available. Skipping ECDSA baseline.")
            print("          Install with: pip install cryptography or pip install ecdsa")
    
    for algorithm in args.algorithms:
        if algorithm not in ALL_ALGORITHMS:
            print(f"[WARNING] Unknown algorithm: {algorithm}, skipping...")
            continue
        
        try:
            result = benchmark_algorithm(algorithm, args.iterations, not args.skip_gas)
            if result:
                all_results.append(result)
        except Exception as e:
            print(f"[ERROR] Benchmarking {algorithm} failed: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_results:
        print("\n[ERROR] No benchmark results collected")
        sys.exit(1)
    
    # Save results
    results_file = save_benchmark_results(all_results)
    
    # Generate comparison table
    comparison_table = generate_comparison_table(all_results)
    
    # Summary
    print("\n" + "="*70)
    print("BENCHMARK SUMMARY")
    print("="*70)
    print(f"Algorithms benchmarked: {len(all_results)}")
    print(f"Results saved to: {results_file}")
    print(f"Comparison table generated")
    print("="*70)
    
    print("\n[SUCCESS] Benchmarking completed!")
    print("\nNext steps:")
    print("  1. Review benchmark results in JSON file")
    print("  2. Run analysis: python scripts/analyze_results.py")
    print("  3. Generate report: python scripts/generate_report.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Benchmarking interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Benchmarking failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
