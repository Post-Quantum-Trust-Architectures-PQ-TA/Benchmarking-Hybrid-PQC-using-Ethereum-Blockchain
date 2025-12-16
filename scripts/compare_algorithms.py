"""
Algorithm Comparison Tool for Research Paper
Generates comprehensive comparison matrices and analysis
"""
import os
import sys
import json
import csv
from datetime import datetime

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "benchmarks")

# NIST Security Levels
NIST_LEVELS = {
    "dilithium2": "Level 2",
    "dilithium3": "Level 3",
    "dilithium5": "Level 5",
    "sphincs128f": "Level 1",
    "sphincs_fast": "Level 3/5",
    "falcon512": "Level 1",
    "falcon1024": "Level 5",
    "ecdsa": "Classical",
}

# Algorithm categories
ALGORITHM_CATEGORIES = {
    "dilithium2": "Lattice-based (ML-DSA)",
    "dilithium3": "Lattice-based (ML-DSA)",
    "dilithium5": "Lattice-based (ML-DSA)",
    "sphincs128f": "Hash-based (SLH-DSA)",
    "sphincs_fast": "Hash-based (SLH-DSA)",
    "falcon512": "Lattice-based (FALCON)",
    "falcon1024": "Lattice-based (FALCON)",
    "ecdsa": "Elliptic Curve (Classical)",
}

def load_latest_benchmark():
    """Load the most recent benchmark results"""
    if not os.path.exists(RESULTS_DIR):
        return None
    
    benchmark_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("benchmark_") and f.endswith(".json")]
    if not benchmark_files:
        return None
    
    latest_file = sorted(benchmark_files)[-1]
    filepath = os.path.join(RESULTS_DIR, latest_file)
    
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_comparison_matrix(benchmark_data):
    """
    Generate comprehensive comparison matrix for research paper
    
    Args:
        benchmark_data: Loaded benchmark JSON data
    
    Returns:
        dict: Comparison matrix data
    """
    print("="*70)
    print("ALGORITHM COMPARISON MATRIX")
    print("="*70)
    
    results = benchmark_data.get('results', [])
    
    comparison = []
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        keygen = result.get('key_generation', {})
        signing = result.get('signing', {})
        verify = result.get('verification', {})
        gas = result.get('gas_usage', {})
        
        comparison.append({
            'algorithm': algo,
            'category': ALGORITHM_CATEGORIES.get(algo, 'Unknown'),
            'nist_level': NIST_LEVELS.get(algo, 'Unknown'),
            'keygen_mean_ms': keygen.get('mean', 0) * 1000 if keygen else 0,
            'keygen_std_ms': keygen.get('std_dev', 0) * 1000 if keygen else 0,
            'sign_mean_ms': signing.get('mean', 0) * 1000 if signing else 0,
            'sign_std_ms': signing.get('std_dev', 0) * 1000 if signing else 0,
            'verify_mean_ms': verify.get('mean', 0) * 1000 if verify else 0,
            'verify_std_ms': verify.get('std_dev', 0) * 1000 if verify else 0,
            'public_key_bytes': keygen.get('public_key_size', 0) if keygen else 0,
            'private_key_bytes': keygen.get('private_key_size', 0) if keygen else 0,
            'signature_bytes': signing.get('signature_size', 0) if signing else 0,
            'registration_gas': gas.get('registration_gas', 0) if gas else 0,
            'transaction_gas': gas.get('transaction_gas', 0) if gas else 0,
        })
    
    return comparison

def generate_latex_table(comparison_data):
    """
    Generate LaTeX table for research paper
    
    Args:
        comparison_data: Comparison matrix data
    
    Returns:
        str: LaTeX table code
    """
    latex = "\\begin{table}[h]\n"
    latex += "\\centering\n"
    latex += "\\caption{Performance Comparison of PQC Signature Algorithms}\n"
    latex += "\\label{tab:pqc_comparison}\n"
    latex += "\\begin{tabular}{|l|c|c|c|c|c|c|}\n"
    latex += "\\hline\n"
    latex += "Algorithm & Keygen (ms) & Sign (ms) & Verify (ms) & PubKey (B) & Sig (B) & Gas (K) \\\\\n"
    latex += "\\hline\n"
    
    for data in comparison_data:
        algo = data['algorithm'].replace('_', '\\_')
        keygen = f"{data['keygen_mean_ms']:.2f}"
        sign = f"{data['sign_mean_ms']:.2f}"
        verify = f"{data['verify_mean_ms']:.2f}"
        pubkey = f"{data['public_key_bytes']}"
        sig = f"{data['signature_bytes']}"
        gas = f"{data['transaction_gas']/1000:.1f}" if data['transaction_gas'] > 0 else "N/A"
        
        latex += f"{algo} & {keygen} & {sign} & {verify} & {pubkey} & {sig} & {gas} \\\\\n"
    
    latex += "\\hline\n"
    latex += "\\end{tabular}\n"
    latex += "\\end{table}\n"
    
    return latex

def generate_csv_comparison(comparison_data, output_file):
    """Generate CSV comparison file"""
    if not comparison_data:
        return
    
    fieldnames = [
        'algorithm', 'category', 'nist_level',
        'keygen_mean_ms', 'keygen_std_ms',
        'sign_mean_ms', 'sign_std_ms',
        'verify_mean_ms', 'verify_std_ms',
        'public_key_bytes', 'private_key_bytes', 'signature_bytes',
        'registration_gas', 'transaction_gas'
    ]
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(comparison_data)
    
    print(f"[OK] CSV comparison saved to: {output_file}")

def print_comparison_table(comparison_data):
    """Print formatted comparison table"""
    print("\n" + "="*100)
    print(f"{'Algorithm':<15} {'Category':<20} {'NIST':<8} {'Keygen':<12} {'Sign':<12} {'Verify':<12} {'PubKey':<10} {'Sig':<10} {'Gas':<10}")
    print("="*100)
    
    for data in comparison_data:
        algo = data['algorithm']
        cat = data['category'][:19]
        nist = data['nist_level']
        keygen = f"{data['keygen_mean_ms']:.2f}±{data['keygen_std_ms']:.2f}"
        sign = f"{data['sign_mean_ms']:.2f}±{data['sign_std_ms']:.2f}"
        verify = f"{data['verify_mean_ms']:.2f}±{data['verify_std_ms']:.2f}"
        pubkey = f"{data['public_key_bytes']}"
        sig = f"{data['signature_bytes']}"
        gas = f"{data['transaction_gas']/1000:.1f}K" if data['transaction_gas'] > 0 else "N/A"
        
        print(f"{algo:<15} {cat:<20} {nist:<8} {keygen:<12} {sign:<12} {verify:<12} {pubkey:<10} {sig:<10} {gas:<10}")
    
    print("="*100)

def generate_insights(comparison_data):
    """Generate research insights and recommendations"""
    print("\n" + "="*70)
    print("RESEARCH INSIGHTS")
    print("="*70)
    
    # Find fastest/smallest/best
    fastest_keygen = min(comparison_data, key=lambda x: x['keygen_mean_ms'])
    fastest_sign = min(comparison_data, key=lambda x: x['sign_mean_ms'])
    fastest_verify = min(comparison_data, key=lambda x: x['verify_mean_ms'])
    smallest_pubkey = min(comparison_data, key=lambda x: x['public_key_bytes'])
    smallest_sig = min(comparison_data, key=lambda x: x['signature_bytes'])
    lowest_gas = min([x for x in comparison_data if x['transaction_gas'] > 0], 
                     key=lambda x: x['transaction_gas'], default=None)
    
    print("\nPerformance Leaders:")
    print(f"  Fastest Key Generation: {fastest_keygen['algorithm']} ({fastest_keygen['keygen_mean_ms']:.2f} ms)")
    print(f"  Fastest Signing: {fastest_sign['algorithm']} ({fastest_sign['sign_mean_ms']:.2f} ms)")
    print(f"  Fastest Verification: {fastest_verify['algorithm']} ({fastest_verify['verify_mean_ms']:.2f} ms)")
    print(f"  Smallest Public Key: {smallest_pubkey['algorithm']} ({smallest_pubkey['public_key_bytes']} bytes)")
    print(f"  Smallest Signature: {smallest_sig['algorithm']} ({smallest_sig['signature_bytes']} bytes)")
    if lowest_gas:
        print(f"  Lowest Gas Usage: {lowest_gas['algorithm']} ({lowest_gas['transaction_gas']/1000:.1f}K gas)")
    
    print("\nRecommendations:")
    print("  - For high-speed applications: Consider fastest algorithms")
    print("  - For storage-constrained: Consider smallest key/signature sizes")
    print("  - For blockchain: Consider gas-efficient options")
    print("  - For security: Use NIST Level 3+ algorithms")

def main():
    """Main comparison function"""
    print("="*70)
    print("  PQC ALGORITHM COMPARISON TOOL")
    print("  For Research Paper Publication")
    print("="*70)
    print()
    
    # Load benchmark data
    benchmark_data = load_latest_benchmark()
    if not benchmark_data:
        print("[ERROR] No benchmark data found")
        print("        Run: python scripts/benchmark.py first")
        sys.exit(1)
    
    print(f"[OK] Loaded benchmark data from: {benchmark_data.get('benchmark_date', 'unknown')}")
    print(f"     Algorithms: {benchmark_data.get('total_algorithms', 0)}")
    print()
    
    # Generate comparison matrix
    comparison_data = generate_comparison_matrix(benchmark_data)
    
    # Print comparison table
    print_comparison_table(comparison_data)
    
    # Generate LaTeX table
    latex_table = generate_latex_table(comparison_data)
    latex_file = os.path.join(RESULTS_DIR, "comparison_table.tex")
    with open(latex_file, 'w') as f:
        f.write(latex_table)
    print(f"\n[OK] LaTeX table saved to: {latex_file}")
    
    # Generate CSV
    csv_file = os.path.join(RESULTS_DIR, "comparison_matrix.csv")
    generate_csv_comparison(comparison_data, csv_file)
    
    # Generate insights
    generate_insights(comparison_data)
    
    print("\n" + "="*70)
    print("[SUCCESS] Comparison analysis completed!")
    print("="*70)

if __name__ == "__main__":
    main()

