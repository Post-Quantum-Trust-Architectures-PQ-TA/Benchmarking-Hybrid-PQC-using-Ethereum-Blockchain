"""
Batch Operations for Scalability Analysis
Tests performance with different batch sizes: 1, 2, 4, 8, 16, 32, ..., 1024, 2048
"""
import os
import sys
import time
import statistics
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Try to import progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Note: tqdm not available. Install with: pip install tqdm for progress bars")

# Configuration
GANACHE_URL = "http://127.0.0.1:8545"
RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "benchmarks")
BATCH_RESULTS_FILE = os.path.join(RESULTS_DIR, f"batch_operations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

# Batch sizes for scalability testing: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048
BATCH_SIZES = [2**i for i in range(0, 12)]  # 1 to 2048

def ensure_results_directory():
    """Ensure benchmark results directory exists"""
    os.makedirs(RESULTS_DIR, exist_ok=True)

def batch_key_generation(algorithm, batch_size, parallel=False):
    """
    Generate multiple keys in a batch
    
    Args:
        algorithm: Algorithm name
        batch_size: Number of keys to generate
        parallel: Whether to use parallel processing
    
    Returns:
        dict: Results with timing and statistics
    """
    print(f"  Generating {batch_size} {algorithm} keys...")
    
    if not QUANTCRYPT_AVAILABLE:
        return None
    
    keys = []
    times = []
    
    start_total = time.perf_counter()
    
    if parallel and batch_size > 4:
        # Use parallel processing for large batches
        def generate_one_key():
            start = time.perf_counter()
            pk, sk, alg = generate_pqc_keypair(algorithm)
            elapsed = time.perf_counter() - start
            return (pk, sk, alg), elapsed
        
        with ThreadPoolExecutor(max_workers=min(4, batch_size)) as executor:
            futures = [executor.submit(generate_one_key) for _ in range(batch_size)]
            
            iterator = tqdm(futures, desc=f"    Generating keys", disable=not TQDM_AVAILABLE) if TQDM_AVAILABLE else futures
            
            for future in iterator:
                try:
                    key_data, elapsed = future.result()
                    keys.append(key_data)
                    times.append(elapsed)
                except Exception as e:
                    print(f"    [ERROR] Key generation failed: {e}")
    else:
        # Sequential processing
        iterator = tqdm(range(batch_size), desc=f"    Generating keys", disable=not TQDM_AVAILABLE) if TQDM_AVAILABLE else range(batch_size)
        
        for i in iterator:
            try:
                start = time.perf_counter()
                pk, sk, alg = generate_pqc_keypair(algorithm)
                elapsed = time.perf_counter() - start
                keys.append((pk, sk, alg))
                times.append(elapsed)
            except Exception as e:
                print(f"    [ERROR] Key generation {i+1} failed: {e}")
    
    total_time = time.perf_counter() - start_total
    
    if not keys:
        return None
    
    return {
        'operation': 'batch_key_generation',
        'algorithm': algorithm,
        'batch_size': batch_size,
        'parallel': parallel,
        'total_time': total_time,
        'avg_time_per_key': statistics.mean(times) if times else 0,
        'total_keys': len(keys),
        'throughput': len(keys) / total_time if total_time > 0 else 0,  # keys per second
        'times': times,
        'mean': statistics.mean(times) if times else 0,
        'median': statistics.median(times) if times else 0,
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times) if times else 0,
        'max': max(times) if times else 0,
        'timestamp': datetime.now().isoformat()
    }

def batch_signing(algorithm, private_keys, messages, parallel=False):
    """
    Sign multiple messages in a batch
    
    Args:
        algorithm: Algorithm name
        private_keys: List of private keys
        messages: List of messages to sign
        parallel: Whether to use parallel processing
    
    Returns:
        dict: Results with timing and statistics
    """
    batch_size = len(messages)
    print(f"  Signing {batch_size} messages with {algorithm}...")
    
    if not QUANTCRYPT_AVAILABLE:
        return None
    
    if len(private_keys) != len(messages):
        print(f"    [ERROR] Mismatch: {len(private_keys)} keys vs {len(messages)} messages")
        return None
    
    alg = get_algorithm_instance(algorithm)
    signatures = []
    times = []
    
    start_total = time.perf_counter()
    
    if parallel and batch_size > 4:
        # Use parallel processing
        def sign_one_message(idx):
            pk, sk, alg_instance = private_keys[idx]
            msg = messages[idx]
            start = time.perf_counter()
            sig, sign_time = sign_message_pqc(alg, sk, msg)
            elapsed = time.perf_counter() - start
            return sig, elapsed
        
        with ThreadPoolExecutor(max_workers=min(4, batch_size)) as executor:
            futures = [executor.submit(sign_one_message, i) for i in range(batch_size)]
            
            iterator = tqdm(futures, desc=f"    Signing messages", disable=not TQDM_AVAILABLE) if TQDM_AVAILABLE else futures
            
            for i, future in enumerate(iterator):
                try:
                    sig, elapsed = future.result()
                    signatures.append(sig)
                    times.append(elapsed)
                except Exception as e:
                    print(f"    [ERROR] Signing {i+1} failed: {e}")
    else:
        # Sequential processing
        iterator = tqdm(zip(private_keys, messages), total=batch_size, desc=f"    Signing messages", disable=not TQDM_AVAILABLE) if TQDM_AVAILABLE else zip(private_keys, messages)
        
        for (pk, sk, alg_instance), msg in iterator:
            try:
                sig, sign_time = sign_message_pqc(alg, sk, msg)
                signatures.append(sig)
                times.append(sign_time)
            except Exception as e:
                print(f"    [ERROR] Signing failed: {e}")
    
    total_time = time.perf_counter() - start_total
    
    if not signatures:
        return None
    
    return {
        'operation': 'batch_signing',
        'algorithm': algorithm,
        'batch_size': batch_size,
        'parallel': parallel,
        'total_time': total_time,
        'avg_time_per_sign': statistics.mean(times) if times else 0,
        'total_signatures': len(signatures),
        'throughput': len(signatures) / total_time if total_time > 0 else 0,  # signatures per second
        'times': times,
        'mean': statistics.mean(times) if times else 0,
        'median': statistics.median(times) if times else 0,
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times) if times else 0,
        'max': max(times) if times else 0,
        'timestamp': datetime.now().isoformat()
    }

def batch_verification(algorithm, public_keys, messages, signatures, parallel=False):
    """
    Verify multiple signatures in a batch
    
    Args:
        algorithm: Algorithm name
        public_keys: List of public keys
        messages: List of messages
        signatures: List of signatures
        parallel: Whether to use parallel processing
    
    Returns:
        dict: Results with timing and statistics
    """
    batch_size = len(signatures)
    print(f"  Verifying {batch_size} signatures with {algorithm}...")
    
    if not QUANTCRYPT_AVAILABLE:
        return None
    
    if not (len(public_keys) == len(messages) == len(signatures)):
        print(f"    [ERROR] Mismatch: {len(public_keys)} keys, {len(messages)} messages, {len(signatures)} signatures")
        return None
    
    times = []
    valid_count = 0
    
    start_total = time.perf_counter()
    
    if parallel and batch_size > 4:
        # Use parallel processing
        def verify_one_signature(pk, msg, sig):
            start = time.perf_counter()
            is_valid, verify_time = verify_pqc_signature(algorithm, pk, msg, sig)
            elapsed = time.perf_counter() - start
            return is_valid, elapsed
        
        with ThreadPoolExecutor(max_workers=min(4, batch_size)) as executor:
            futures = [executor.submit(verify_one_signature, pk, msg, sig) 
                      for pk, msg, sig in zip(public_keys, messages, signatures)]
            
            iterator = tqdm(futures, desc=f"    Verifying signatures", disable=not TQDM_AVAILABLE) if TQDM_AVAILABLE else futures
            
            for future in iterator:
                try:
                    is_valid, elapsed = future.result()
                    if is_valid:
                        times.append(elapsed)
                        valid_count += 1
                except Exception as e:
                    print(f"    [ERROR] Verification failed: {e}")
    else:
        # Sequential processing
        iterator = tqdm(zip(public_keys, messages, signatures), total=batch_size, desc=f"    Verifying signatures", disable=not TQDM_AVAILABLE) if TQDM_AVAILABLE else zip(public_keys, messages, signatures)
        
        for pk, msg, sig in iterator:
            try:
                is_valid, verify_time = verify_pqc_signature(algorithm, pk, msg, sig)
                if is_valid:
                    times.append(verify_time)
                    valid_count += 1
            except Exception as e:
                print(f"    [ERROR] Verification failed: {e}")
    
    total_time = time.perf_counter() - start_total
    
    if not times:
        return None
    
    return {
        'operation': 'batch_verification',
        'algorithm': algorithm,
        'batch_size': batch_size,
        'parallel': parallel,
        'total_time': total_time,
        'avg_time_per_verify': statistics.mean(times) if times else 0,
        'total_signatures': batch_size,
        'valid_signatures': valid_count,
        'throughput': valid_count / total_time if total_time > 0 else 0,  # verifications per second
        'times': times,
        'mean': statistics.mean(times) if times else 0,
        'median': statistics.median(times) if times else 0,
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'min': min(times) if times else 0,
        'max': max(times) if times else 0,
        'timestamp': datetime.now().isoformat()
    }

def test_batch_scalability(algorithm, batch_sizes=None, parallel=False, test_signing=True, test_verification=True):
    """
    Test scalability with different batch sizes
    
    Args:
        algorithm: Algorithm name
        batch_sizes: List of batch sizes to test (default: BATCH_SIZES)
        parallel: Whether to use parallel processing
        test_signing: Whether to test batch signing
        test_verification: Whether to test batch verification
    
    Returns:
        dict: Complete scalability test results
    """
    if batch_sizes is None:
        batch_sizes = BATCH_SIZES
    
    print(f"\n{'='*70}")
    print(f"BATCH SCALABILITY TEST: {algorithm.upper()}")
    print(f"{'='*70}")
    print(f"Batch sizes: {batch_sizes}")
    print(f"Parallel processing: {parallel}")
    print()
    
    results = {
        'algorithm': algorithm,
        'timestamp': datetime.now().isoformat(),
        'batch_sizes': batch_sizes,
        'parallel': parallel,
        'key_generation': [],
        'signing': [],
        'verification': []
    }
    
    # Test key generation scalability
    print("="*70)
    print("BATCH KEY GENERATION SCALABILITY")
    print("="*70)
    
    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")
        result = batch_key_generation(algorithm, batch_size, parallel)
        if result:
            results['key_generation'].append(result)
            print(f"  Total time: {result['total_time']:.4f}s")
            print(f"  Throughput: {result['throughput']:.2f} keys/sec")
            print(f"  Avg time per key: {result['avg_time_per_key']*1000:.2f}ms")
        else:
            print(f"  [FAIL] Batch size {batch_size} failed")
    
    # Test signing scalability (if requested)
    if test_signing:
        print("\n" + "="*70)
        print("BATCH SIGNING SCALABILITY")
        print("="*70)
        
        # Generate keys and messages for signing tests
        print("\nPreparing keys and messages for signing tests...")
        all_keys = []
        all_messages = []
        
        max_batch = max(batch_sizes)
        for i in range(max_batch):
            try:
                pk, sk, alg = generate_pqc_keypair(algorithm)
                all_keys.append((pk, sk, alg))
                all_messages.append(f"Batch test message {i+1}".encode('utf-8'))
            except Exception as e:
                print(f"  [ERROR] Failed to prepare key {i+1}: {e}")
                break
        
        for batch_size in batch_sizes:
            if batch_size > len(all_keys):
                print(f"\n[SKIP] Batch size {batch_size} (insufficient keys)")
                continue
            
            print(f"\nTesting batch size: {batch_size}")
            keys_batch = all_keys[:batch_size]
            messages_batch = all_messages[:batch_size]
            
            result = batch_signing(algorithm, keys_batch, messages_batch, parallel)
            if result:
                results['signing'].append(result)
                print(f"  Total time: {result['total_time']:.4f}s")
                print(f"  Throughput: {result['throughput']:.2f} signatures/sec")
                print(f"  Avg time per sign: {result['avg_time_per_sign']*1000:.2f}ms")
            else:
                print(f"  [FAIL] Batch size {batch_size} failed")
    
    # Test verification scalability (if requested)
    if test_verification:
        print("\n" + "="*70)
        print("BATCH VERIFICATION SCALABILITY")
        print("="*70)
        
        # Generate keys, messages, and signatures for verification tests
        print("\nPreparing keys, messages, and signatures for verification tests...")
        all_pubkeys = []
        all_messages = []
        all_signatures = []
        
        max_batch = max(batch_sizes)
        alg = get_algorithm_instance(algorithm)
        
        for i in range(max_batch):
            try:
                pk, sk, alg_instance = generate_pqc_keypair(algorithm)
                msg = f"Batch verification test message {i+1}".encode('utf-8')
                sig, _ = sign_message_pqc(alg, sk, msg)
                
                all_pubkeys.append(pk)
                all_messages.append(msg)
                all_signatures.append(sig)
            except Exception as e:
                print(f"  [ERROR] Failed to prepare verification data {i+1}: {e}")
                break
        
        for batch_size in batch_sizes:
            if batch_size > len(all_signatures):
                print(f"\n[SKIP] Batch size {batch_size} (insufficient data)")
                continue
            
            print(f"\nTesting batch size: {batch_size}")
            pubkeys_batch = all_pubkeys[:batch_size]
            messages_batch = all_messages[:batch_size]
            signatures_batch = all_signatures[:batch_size]
            
            result = batch_verification(algorithm, pubkeys_batch, messages_batch, signatures_batch, parallel)
            if result:
                results['verification'].append(result)
                print(f"  Total time: {result['total_time']:.4f}s")
                print(f"  Throughput: {result['throughput']:.2f} verifications/sec")
                print(f"  Valid signatures: {result['valid_signatures']}/{result['total_signatures']}")
                print(f"  Avg time per verify: {result['avg_time_per_verify']*1000:.2f}ms")
            else:
                print(f"  [FAIL] Batch size {batch_size} failed")
    
    return results

def save_batch_results(all_results):
    """Save batch operation results to JSON file"""
    ensure_results_directory()
    
    output = {
        'test_date': datetime.now().isoformat(),
        'total_algorithms': len(all_results),
        'results': all_results
    }
    
    with open(BATCH_RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n[OK] Batch results saved to: {BATCH_RESULTS_FILE}")
    return BATCH_RESULTS_FILE

def generate_scalability_chart(batch_results):
    """Generate scalability analysis chart"""
    print("\n" + "="*70)
    print("SCALABILITY ANALYSIS")
    print("="*70)
    
    for result in batch_results:
        algo = result.get('algorithm', 'unknown')
        print(f"\n{algo.upper()}:")
        
        # Key generation scalability
        if result.get('key_generation'):
            print("\n  Key Generation Throughput:")
            for kg_result in result['key_generation']:
                batch_size = kg_result['batch_size']
                throughput = kg_result['throughput']
                print(f"    Batch {batch_size:4d}: {throughput:8.2f} keys/sec")
        
        # Signing scalability
        if result.get('signing'):
            print("\n  Signing Throughput:")
            for sign_result in result['signing']:
                batch_size = sign_result['batch_size']
                throughput = sign_result['throughput']
                print(f"    Batch {batch_size:4d}: {throughput:8.2f} signatures/sec")
        
        # Verification scalability
        if result.get('verification'):
            print("\n  Verification Throughput:")
            for verify_result in result['verification']:
                batch_size = verify_result['batch_size']
                throughput = verify_result['throughput']
                print(f"    Batch {batch_size:4d}: {throughput:8.2f} verifications/sec")

def main():
    """Main batch operations function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Batch Operations for Scalability Analysis"
    )
    parser.add_argument(
        "--algorithm",
        type=str,
        default="dilithium3",
        help="Algorithm to test (default: dilithium3)"
    )
    parser.add_argument(
        "--batch-sizes",
        nargs="+",
        type=int,
        default=None,
        help="Custom batch sizes (default: 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048)"
    )
    parser.add_argument(
        "--max-batch",
        type=int,
        default=2048,
        help="Maximum batch size (default: 2048)"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Use parallel processing"
    )
    parser.add_argument(
        "--skip-signing",
        action="store_true",
        help="Skip batch signing tests"
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip batch verification tests"
    )
    
    args = parser.parse_args()
    
    # Determine batch sizes
    if args.batch_sizes:
        batch_sizes = sorted(args.batch_sizes)
    else:
        # Generate exponential batch sizes up to max_batch
        batch_sizes = []
        i = 0
        while 2**i <= args.max_batch:
            batch_sizes.append(2**i)
            i += 1
    
    print("="*70)
    print("  BATCH OPERATIONS FOR SCALABILITY ANALYSIS")
    print("="*70)
    print(f"\nAlgorithm: {args.algorithm}")
    print(f"Batch sizes: {batch_sizes}")
    print(f"Parallel processing: {args.parallel}")
    print(f"Test signing: {not args.skip_signing}")
    print(f"Test verification: {not args.skip_verification}")
    print()
    
    if not QUANTCRYPT_AVAILABLE:
        print("[ERROR] QuantCrypt library not available")
        print("        Install with: pip install quantcrypt")
        sys.exit(1)
    
    # Run scalability test
    results = test_batch_scalability(
        args.algorithm,
        batch_sizes=batch_sizes,
        parallel=args.parallel,
        test_signing=not args.skip_signing,
        test_verification=not args.skip_verification
    )
    
    if not results:
        print("\n[ERROR] Batch scalability test failed")
        sys.exit(1)
    
    # Save results
    results_file = save_batch_results([results])
    
    # Generate scalability analysis
    generate_scalability_chart([results])
    
    print("\n" + "="*70)
    print("BATCH OPERATIONS SUMMARY")
    print("="*70)
    print(f"Algorithm: {args.algorithm}")
    print(f"Results saved to: {results_file}")
    print("="*70)
    
    print("\n[SUCCESS] Batch operations completed!")
    print("\nNext steps:")
    print("  1. Review batch results in JSON file")
    print("  2. Analyze scalability trends")
    print("  3. Generate scalability charts (if matplotlib available)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Batch operations interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Batch operations failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

