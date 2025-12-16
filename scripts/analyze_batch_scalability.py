"""
Analyze Batch Scalability Results
Generates charts and analysis for batch operation scalability
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
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")

def load_latest_batch_results():
    """Load the most recent batch results"""
    if not os.path.exists(RESULTS_DIR):
        return None
    
    batch_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("batch_operations_") and f.endswith(".json")]
    if not batch_files:
        return None
    
    latest_file = sorted(batch_files)[-1]
    filepath = os.path.join(RESULTS_DIR, latest_file)
    
    with open(filepath, 'r') as f:
        return json.load(f)

def load_all_batch_results():
    """Load all batch result files"""
    if not os.path.exists(RESULTS_DIR):
        return []
    
    batch_files = [f for f in os.listdir(RESULTS_DIR) if f.startswith("batch_operations_") and f.endswith(".json")]
    if not batch_files:
        return []
    
    all_data = []
    for batch_file in sorted(batch_files):
        filepath = os.path.join(RESULTS_DIR, batch_file)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                all_data.append(data)
        except Exception as e:
            print(f"[WARNING] Failed to load {batch_file}: {e}")
    
    return all_data

def create_scalability_chart(batch_data, operation='key_generation', save_path=None):
    """
    Create scalability chart showing throughput vs batch size
    
    Args:
        batch_data: Batch results data
        operation: Operation type ('key_generation', 'signing', 'verification')
        save_path: Path to save figure
    """
    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] Matplotlib not available")
        return None
    
    results = batch_data.get('results', [])
    if not results:
        return None
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        op_data = result.get(operation, [])
        
        if not op_data:
            continue
        
        batch_sizes = [d['batch_size'] for d in op_data]
        throughputs = [d['throughput'] for d in op_data]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax.plot(batch_sizes, throughputs, marker='o', linewidth=2, markersize=8, label=f'{algo.upper()}')
        ax.set_xlabel('Batch Size', fontsize=12, fontweight='bold')
        ax.set_ylabel('Throughput (operations/sec)', fontsize=12, fontweight='bold')
        ax.set_title(f'Scalability Analysis: {operation.replace("_", " ").title()}', 
                     fontsize=14, fontweight='bold')
        ax.set_xscale('log', base=2)
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        plt.tight_layout()
        
        if save_path is None:
            os.makedirs(FIGURES_DIR, exist_ok=True)
            save_path = os.path.join(FIGURES_DIR, f'scalability_{operation}_{algo}.png')
        
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[OK] Scalability chart saved to: {save_path}")
        return save_path

def create_combined_scalability_chart(all_batch_data, operation='key_generation', save_path=None):
    """
    Create combined scalability chart showing multiple algorithms on same plot
    
    Args:
        all_batch_data: List of batch results data (one per algorithm)
        operation: Operation type ('key_generation', 'signing', 'verification')
        save_path: Path to save figure
    """
    if not MATPLOTLIB_AVAILABLE:
        print("[SKIP] Matplotlib not available")
        return None
    
    if not all_batch_data:
        return None
    
    # Algorithm colors and markers for better distinction
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p']
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    algo_count = 0
    for batch_data in all_batch_data:
        results = batch_data.get('results', [])
        if not results:
            continue
        
        for result in results:
            algo = result.get('algorithm', 'unknown')
            op_data = result.get(operation, [])
            
            if not op_data:
                continue
            
            batch_sizes = [d['batch_size'] for d in op_data]
            throughputs = [d['throughput'] for d in op_data]
            
            # Use different color and marker for each algorithm
            color = colors[algo_count % len(colors)]
            marker = markers[algo_count % len(markers)]
            
            # Format algorithm name for display
            algo_display = algo.upper().replace('_', '-')
            if algo == 'dilithium3':
                algo_display = 'Dilithium3 (ML-DSA-65)'
            elif algo == 'falcon512':
                algo_display = 'FALCON-512'
            elif algo == 'sphincs_fast':
                algo_display = 'SPHINCS+ Fast'
            elif algo == 'sphincs128f':
                algo_display = 'SPHINCS+ Small'
            
            ax.plot(batch_sizes, throughputs, marker=marker, linewidth=2.5, 
                   markersize=8, label=algo_display, color=color, alpha=0.8)
            
            algo_count += 1
    
    if algo_count == 0:
        print(f"[WARNING] No data found for {operation}")
        plt.close()
        return None
    
    ax.set_xlabel('Batch Size', fontsize=13, fontweight='bold')
    ax.set_ylabel('Throughput (operations/sec)', fontsize=13, fontweight='bold')
    ax.set_title(f'Combined Scalability Analysis: {operation.replace("_", " ").title()}', 
                 fontsize=15, fontweight='bold', pad=15)
    ax.set_xscale('log', base=2)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=11, framealpha=0.9)
    
    # Add minor grid for better readability
    ax.grid(True, which='minor', alpha=0.2, linestyle=':')
    
    plt.tight_layout()
    
    if save_path is None:
        os.makedirs(FIGURES_DIR, exist_ok=True)
        save_path = os.path.join(FIGURES_DIR, f'scalability_{operation}_combined.png')
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] Combined scalability chart saved to: {save_path}")
    return save_path

def generate_combined_scalability_charts():
    """Generate combined scalability charts for all available algorithms"""
    all_batch_data = load_all_batch_results()
    
    if not all_batch_data:
        print("[ERROR] No batch data files found")
        print("        Run: python scripts/batch_operations.py first")
        return []
    
    print("="*70)
    print("  GENERATING COMBINED SCALABILITY CHARTS")
    print("="*70)
    print(f"Found {len(all_batch_data)} batch result file(s)")
    
    figures = []
    operations = ['key_generation', 'signing', 'verification']
    
    for operation in operations:
        print(f"\nGenerating combined {operation} scalability chart...")
        fig = create_combined_scalability_chart(all_batch_data, operation)
        if fig:
            figures.append(fig)
    
    print(f"\n[SUCCESS] Generated {len(figures)} combined chart(s)")
    return figures

def generate_all_scalability_charts(batch_data=None):
    """Generate all scalability charts"""
    if batch_data is None:
        batch_data = load_latest_batch_results()
        if not batch_data:
            print("[ERROR] No batch data found")
            return []
    
    print("="*70)
    print("  GENERATING SCALABILITY CHARTS")
    print("="*70)
    
    figures = []
    
    operations = ['key_generation', 'signing', 'verification']
    
    for operation in operations:
        print(f"\nGenerating {operation} scalability chart...")
        fig = create_scalability_chart(batch_data, operation)
        if fig:
            figures.append(fig)
    
    print(f"\n[SUCCESS] Generated {len(figures)} chart(s)")
    return figures

def print_scalability_analysis(batch_data):
    """Print scalability analysis"""
    results = batch_data.get('results', [])
    
    print("\n" + "="*70)
    print("SCALABILITY ANALYSIS SUMMARY")
    print("="*70)
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        print(f"\n{algo.upper()}:")
        
        # Key generation
        if result.get('key_generation'):
            print("\n  Key Generation:")
            print(f"    {'Batch Size':<12} {'Throughput (ops/sec)':<20} {'Total Time (s)':<15} {'Avg/Key (ms)':<15}")
            print("    " + "-" * 60)
            for kg in result['key_generation']:
                print(f"    {kg['batch_size']:<12} {kg['throughput']:<20.2f} {kg['total_time']:<15.4f} {kg['avg_time_per_key']*1000:<15.2f}")
        
        # Signing
        if result.get('signing'):
            print("\n  Signing:")
            print(f"    {'Batch Size':<12} {'Throughput (ops/sec)':<20} {'Total Time (s)':<15} {'Avg/Sign (ms)':<15}")
            print("    " + "-" * 60)
            for sign in result['signing']:
                print(f"    {sign['batch_size']:<12} {sign['throughput']:<20.2f} {sign['total_time']:<15.4f} {sign['avg_time_per_sign']*1000:<15.2f}")
        
        # Verification
        if result.get('verification'):
            print("\n  Verification:")
            print(f"    {'Batch Size':<12} {'Throughput (ops/sec)':<20} {'Total Time (s)':<15} {'Avg/Verify (ms)':<15} {'Valid':<10}")
            print("    " + "-" * 70)
            for verify in result['verification']:
                print(f"    {verify['batch_size']:<12} {verify['throughput']:<20.2f} {verify['total_time']:<15.4f} {verify['avg_time_per_verify']*1000:<15.2f} {verify['valid_signatures']}/{verify['total_signatures']}")

def main():
    """Main analysis function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze Batch Scalability Results"
    )
    parser.add_argument(
        "--batch-file",
        type=str,
        default=None,
        help="Path to batch results JSON file (default: latest)"
    )
    parser.add_argument(
        "--no-charts",
        action="store_true",
        help="Skip chart generation"
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Generate combined charts for all algorithms"
    )
    
    args = parser.parse_args()
    
    # Load batch data
    if args.batch_file:
        with open(args.batch_file, 'r') as f:
            batch_data = json.load(f)
    else:
        batch_data = load_latest_batch_results()
        if not batch_data:
            print("[ERROR] No batch data found")
            print("        Run: python scripts/batch_operations.py first")
            sys.exit(1)
    
    print(f"[OK] Loaded batch data from: {batch_data.get('test_date', 'unknown')}")
    
    # Print analysis
    print_scalability_analysis(batch_data)
    
    # Generate charts
    if not args.no_charts:
        if args.combined:
            # Generate combined charts for all algorithms
            figures = generate_combined_scalability_charts()
        else:
            # Generate individual charts
            figures = generate_all_scalability_charts(batch_data)
        
        if figures:
            print("\nGenerated figures:")
            for fig in figures:
                print(f"  - {fig}")

if __name__ == "__main__":
    main()

