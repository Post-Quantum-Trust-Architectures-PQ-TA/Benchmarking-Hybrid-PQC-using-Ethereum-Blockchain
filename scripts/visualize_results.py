"""
Visualization Tool for Research Paper
Generates publication-ready charts and graphs
"""
import os
import sys
import json
from datetime import datetime

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

sys.path.insert(0, os.path.join(PROJECT_ROOT, "scripts"))

RESULTS_DIR = os.path.join(PROJECT_ROOT, "data", "benchmarks")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "data", "figures")

# Try to import matplotlib
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")
    print("         Charts will not be generated.")

def ensure_figures_directory():
    """Ensure figures directory exists"""
    os.makedirs(FIGURES_DIR, exist_ok=True)

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

def add_value_labels_to_bars(ax, bars, values, is_size_chart=False):
    """
    Add value labels on top of bars, with special handling for small values
    
    Args:
        ax: Matplotlib axes object
        bars: List of bar objects
        values: List of values corresponding to bars
        is_size_chart: If True, format as bytes; if False, format as time in ms
    """
    for bar, value in zip(bars, values):
        height = bar.get_height()
        if height > 0:
            # Format label based on value type and size
            if is_size_chart:
                # Format as bytes
                if value < 100:
                    label = f'{int(value)}B'
                elif value < 1000:
                    label = f'{int(value)}B'
                else:
                    label = f'{value/1000:.1f}KB' if value < 10000 else f'{int(value/1000)}KB'
            else:
                # Format as time in milliseconds
                if value < 0.1:  # Very small values (< 0.1 ms)
                    label = f'{value:.3f}'
                elif value < 1:  # Small values (< 1 ms)
                    label = f'{value:.2f}'
                elif value < 10:  # Medium values (< 10 ms)
                    label = f'{value:.2f}'
                else:  # Large values
                    label = f'{value:.1f}'
            
            # Position label above bar, or inside if bar is too small
            max_val = max([v for v in values if v > 0])
            if height < max_val * 0.02:  # If bar is less than 2% of max
                # Place label inside bar at the top
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       label, ha='center', va='bottom', fontsize=8,
                       fontweight='bold', color='white',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
            else:
                # Place label above bar
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       label, ha='center', va='bottom', fontsize=8,
                       fontweight='bold')

def create_performance_comparison_chart(benchmark_data, save_path=None):
    """
    Create performance comparison bar chart (Keygen, Sign, Verify)
    
    Args:
        benchmark_data: Loaded benchmark JSON data
        save_path: Path to save figure (optional)
    
    Returns:
        str: Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] Matplotlib not available, skipping chart generation")
        return None
    
    results = benchmark_data.get('results', [])
    
    # Extract data
    algorithms = []
    keygen_times = []
    sign_times = []
    verify_times = []
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        keygen = result.get('key_generation', {})
        signing = result.get('signing', {})
        verify = result.get('verification', {})
        
        if keygen and signing and verify:
            algorithms.append(algo.upper().replace('_', '-'))
            keygen_times.append(keygen.get('mean', 0) * 1000)  # Convert to ms
            sign_times.append(signing.get('mean', 0) * 1000)
            verify_times.append(verify.get('mean', 0) * 1000)
    
    if not algorithms:
        print("[ERROR] No valid benchmark data for chart")
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(algorithms))
    width = 0.25
    
    bars1 = ax.bar(x - width, keygen_times, width, label='Key Generation', alpha=0.8)
    bars2 = ax.bar(x, sign_times, width, label='Signing', alpha=0.8)
    bars3 = ax.bar(x + width, verify_times, width, label='Verification', alpha=0.8)
    
    # Add labels to all bars
    add_value_labels_to_bars(ax, bars1, keygen_times, is_size_chart=False)
    add_value_labels_to_bars(ax, bars2, sign_times, is_size_chart=False)
    add_value_labels_to_bars(ax, bars3, verify_times, is_size_chart=False)
    
    ax.set_xlabel('Algorithm', fontsize=12, fontweight='bold')
    ax.set_ylabel('Time (milliseconds)', fontsize=12, fontweight='bold')
    ax.set_title('Performance Comparison: Key Generation, Signing, and Verification', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Use logarithmic scale if there's a large range difference
    max_val = max(max(keygen_times), max(sign_times), max(verify_times))
    min_val = min(min([v for v in keygen_times if v > 0]), 
                  min([v for v in sign_times if v > 0]), 
                  min([v for v in verify_times if v > 0]))
    
    # If range is more than 100x, use log scale
    if max_val / min_val > 100:
        ax.set_yscale('log')
        ax.set_ylabel('Time (milliseconds, log scale)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(FIGURES_DIR, 'performance_comparison.png')
    
    ensure_figures_directory()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] Performance comparison chart saved to: {save_path}")
    return save_path

def create_size_comparison_chart(benchmark_data, save_path=None):
    """
    Create size comparison chart (Public Key, Signature)
    
    Args:
        benchmark_data: Loaded benchmark JSON data
        save_path: Path to save figure (optional)
    
    Returns:
        str: Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] Matplotlib not available, skipping chart generation")
        return None
    
    results = benchmark_data.get('results', [])
    
    # Extract data
    algorithms = []
    pubkey_sizes = []
    sig_sizes = []
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        keygen = result.get('key_generation', {})
        signing = result.get('signing', {})
        
        if keygen and signing:
            algorithms.append(algo.upper().replace('_', '-'))
            pubkey_sizes.append(keygen.get('public_key_size', 0))
            sig_sizes.append(signing.get('signature_size', 0))
    
    if not algorithms:
        print("[ERROR] No valid benchmark data for chart")
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(algorithms))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, pubkey_sizes, width, label='Public Key', alpha=0.8, color='#3498db')
    bars2 = ax.bar(x + width/2, sig_sizes, width, label='Signature', alpha=0.8, color='#e74c3c')
    
    # Add value labels to all bars
    add_value_labels_to_bars(ax, bars1, pubkey_sizes, is_size_chart=True)
    add_value_labels_to_bars(ax, bars2, sig_sizes, is_size_chart=True)
    
    ax.set_xlabel('Algorithm', fontsize=12, fontweight='bold')
    ax.set_ylabel('Size (bytes)', fontsize=12, fontweight='bold')
    ax.set_title('Size Comparison: Public Keys and Signatures', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Use logarithmic scale if there's a large range difference
    max_val = max(max(pubkey_sizes), max(sig_sizes))
    min_val = min(min([v for v in pubkey_sizes if v > 0]), 
                  min([v for v in sig_sizes if v > 0]))
    
    # If range is more than 100x, use log scale
    if max_val / min_val > 100:
        ax.set_yscale('log')
        ax.set_ylabel('Size (bytes, log scale)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(FIGURES_DIR, 'size_comparison.png')
    
    ensure_figures_directory()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] Size comparison chart saved to: {save_path}")
    return save_path

def create_gas_cost_chart(benchmark_data, save_path=None):
    """
    Create gas cost comparison chart
    
    Args:
        benchmark_data: Loaded benchmark JSON data
        save_path: Path to save figure (optional)
    
    Returns:
        str: Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] Matplotlib not available, skipping chart generation")
        return None
    
    results = benchmark_data.get('results', [])
    
    # Extract data
    algorithms = []
    reg_gas = []
    tx_gas = []
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        gas = result.get('gas_usage', {})
        
        if gas and gas.get('transaction_gas', 0) > 0:
            algorithms.append(algo.upper().replace('_', '-'))
            reg_gas.append(gas.get('registration_gas', 0) / 1000)  # Convert to K gas
            tx_gas.append(gas.get('transaction_gas', 0) / 1000)
    
    if not algorithms:
        print("[WARNING] No gas usage data available, skipping gas chart")
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(algorithms))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, reg_gas, width, label='Registration', alpha=0.8, color='#9b59b6')
    bars2 = ax.bar(x + width/2, tx_gas, width, label='Transaction', alpha=0.8, color='#f39c12')
    
    # Add value labels to all bars (gas values in K gas)
    def add_gas_labels(bars, values):
        """Add value labels for gas costs in K gas"""
        for bar, value in zip(bars, values):
            height = bar.get_height()
            if height > 0:
                # Format label for gas values
                if value < 1:  # Very small values (< 1K gas)
                    label = f'{value:.2f}K'
                elif value < 10:  # Small values (< 10K gas)
                    label = f'{value:.1f}K'
                else:  # Large values
                    label = f'{int(value)}K' if value < 1000 else f'{value/1000:.1f}M'
                
                # Position label above bar, or inside if bar is too small
                max_val = max([v for v in values if v > 0])
                if height < max_val * 0.02:  # If bar is less than 2% of max
                    # Place label inside bar at the top
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           label, ha='center', va='bottom', fontsize=8,
                           fontweight='bold', color='white',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
                else:
                    # Place label above bar
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           label, ha='center', va='bottom', fontsize=8,
                           fontweight='bold')
    
    add_gas_labels(bars1, reg_gas)
    add_gas_labels(bars2, tx_gas)
    
    ax.set_xlabel('Algorithm', fontsize=12, fontweight='bold')
    ax.set_ylabel('Gas Cost (K gas)', fontsize=12, fontweight='bold')
    ax.set_title('Gas Cost Comparison: Registration and Transaction', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, rotation=45, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Use logarithmic scale if there's a large range difference
    max_val = max(max(reg_gas), max(tx_gas))
    min_val = min(min([v for v in reg_gas if v > 0]), 
                  min([v for v in tx_gas if v > 0]))
    
    # If range is more than 100x, use log scale
    if max_val / min_val > 100:
        ax.set_yscale('log')
        ax.set_ylabel('Gas Cost (K gas, log scale)', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(FIGURES_DIR, 'gas_cost_comparison.png')
    
    ensure_figures_directory()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] Gas cost comparison chart saved to: {save_path}")
    return save_path

def create_pqc_vs_ecdsa_chart(benchmark_data, save_path=None):
    """
    Create PQC vs ECDSA comparison chart
    
    Args:
        benchmark_data: Loaded benchmark JSON data
        save_path: Path to save figure (optional)
    
    Returns:
        str: Path to saved figure
    """
    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] Matplotlib not available, skipping chart generation")
        return None
    
    results = benchmark_data.get('results', [])
    
    # Find ECDSA baseline
    ecdsa_result = None
    pqc_results = []
    
    for result in results:
        if result.get('algorithm') == 'ecdsa':
            ecdsa_result = result
        else:
            pqc_results.append(result)
    
    if not ecdsa_result:
        print("[WARNING] No ECDSA baseline data found, skipping PQC vs ECDSA chart")
        return None
    
    # Extract ECDSA data
    ecdsa_keygen = ecdsa_result.get('key_generation', {}).get('mean', 0) * 1000
    ecdsa_sign = ecdsa_result.get('signing', {}).get('mean', 0) * 1000
    ecdsa_verify = ecdsa_result.get('verification', {}).get('mean', 0) * 1000
    
    # Extract PQC data (average)
    pqc_keygen_times = []
    pqc_sign_times = []
    pqc_verify_times = []
    
    for result in pqc_results:
        keygen = result.get('key_generation', {})
        signing = result.get('signing', {})
        verify = result.get('verification', {})
        
        if keygen and signing and verify:
            pqc_keygen_times.append(keygen.get('mean', 0) * 1000)
            pqc_sign_times.append(signing.get('mean', 0) * 1000)
            pqc_verify_times.append(verify.get('mean', 0) * 1000)
    
    if not pqc_keygen_times:
        print("[ERROR] No PQC data for comparison")
        return None
    
    # Calculate averages
    avg_pqc_keygen = np.mean(pqc_keygen_times)
    avg_pqc_sign = np.mean(pqc_sign_times)
    avg_pqc_verify = np.mean(pqc_verify_times)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    categories = ['Key Generation', 'Signing', 'Verification']
    ecdsa_values = [ecdsa_keygen, ecdsa_sign, ecdsa_verify]
    pqc_values = [avg_pqc_keygen, avg_pqc_sign, avg_pqc_verify]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, ecdsa_values, width, label='ECDSA (Baseline)', alpha=0.8, color='#2ecc71')
    bars2 = ax.bar(x + width/2, pqc_values, width, label='PQC (Average)', alpha=0.8, color='#e74c3c')
    
    # Add value labels to all bars
    add_value_labels_to_bars(ax, bars1, ecdsa_values, is_size_chart=False)
    add_value_labels_to_bars(ax, bars2, pqc_values, is_size_chart=False)
    
    ax.set_ylabel('Time (milliseconds)', fontsize=12, fontweight='bold')
    ax.set_title('PQC vs ECDSA Performance Comparison', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Use logarithmic scale if there's a large range difference
    max_val = max(max(ecdsa_values), max(pqc_values))
    min_val = min(min([v for v in ecdsa_values if v > 0]), 
                  min([v for v in pqc_values if v > 0]))
    
    # If range is more than 100x, use log scale
    if max_val / min_val > 100:
        ax.set_yscale('log')
        ax.set_ylabel('Time (milliseconds, log scale)', fontsize=12, fontweight='bold')
    
    # Add ratio annotations (above value labels)
    for i, (ecdsa_val, pqc_val) in enumerate(zip(ecdsa_values, pqc_values)):
        if ecdsa_val > 0:
            ratio = pqc_val / ecdsa_val
            # Position ratio annotation higher to avoid overlap with value labels
            max_height = max(ecdsa_val, pqc_val)
            ax.text(i, max_height * 1.15, f'{ratio:.1f}x', 
                   ha='center', fontsize=10, fontweight='bold', 
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
    
    plt.tight_layout()
    
    if save_path is None:
        save_path = os.path.join(FIGURES_DIR, 'pqc_vs_ecdsa.png')
    
    ensure_figures_directory()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] PQC vs ECDSA comparison chart saved to: {save_path}")
    return save_path

def generate_all_charts(benchmark_data=None):
    """
    Generate all charts for research paper
    
    Args:
        benchmark_data: Optional benchmark data (loads latest if None)
    
    Returns:
        list: Paths to generated figures
    """
    if benchmark_data is None:
        benchmark_data = load_latest_benchmark()
        if not benchmark_data:
            print("[ERROR] No benchmark data found")
            print("        Run: python scripts/benchmark.py first")
            return []
    
    print("="*70)
    print("  GENERATING RESEARCH PAPER CHARTS")
    print("="*70)
    print()
    
    figures = []
    
    # 1. Performance comparison
    print("1. Generating performance comparison chart...")
    fig1 = create_performance_comparison_chart(benchmark_data)
    if fig1:
        figures.append(fig1)
    
    # 2. Size comparison
    print("2. Generating size comparison chart...")
    fig2 = create_size_comparison_chart(benchmark_data)
    if fig2:
        figures.append(fig2)
    
    # 3. Gas cost comparison
    print("3. Generating gas cost comparison chart...")
    fig3 = create_gas_cost_chart(benchmark_data)
    if fig3:
        figures.append(fig3)
    
    # 4. PQC vs ECDSA
    print("4. Generating PQC vs ECDSA comparison chart...")
    fig4 = create_pqc_vs_ecdsa_chart(benchmark_data)
    if fig4:
        figures.append(fig4)
    
    print("\n" + "="*70)
    print(f"[SUCCESS] Generated {len(figures)} chart(s)")
    print("="*70)
    print("\nGenerated figures:")
    for fig in figures:
        print(f"  - {fig}")
    
    return figures

def main():
    """Main visualization function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate Research Paper Charts and Visualizations"
    )
    parser.add_argument(
        "--benchmark-file",
        type=str,
        default=None,
        help="Path to benchmark JSON file (default: latest)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for figures (default: data/figures)"
    )
    
    args = parser.parse_args()
    
    # Load benchmark data
    if args.benchmark_file:
        with open(args.benchmark_file, 'r') as f:
            benchmark_data = json.load(f)
    else:
        benchmark_data = load_latest_benchmark()
        if not benchmark_data:
            print("[ERROR] No benchmark data found")
            print("        Run: python scripts/benchmark.py first")
            sys.exit(1)
    
    # Set output directory
    if args.output_dir:
        global FIGURES_DIR
        FIGURES_DIR = args.output_dir
    
    # Generate all charts
    figures = generate_all_charts(benchmark_data)
    
    if not figures:
        print("\n[WARNING] No figures were generated")
        if not MATPLOTLIB_AVAILABLE:
            print("         Install matplotlib: pip install matplotlib")
        sys.exit(1)

if __name__ == "__main__":
    main()

