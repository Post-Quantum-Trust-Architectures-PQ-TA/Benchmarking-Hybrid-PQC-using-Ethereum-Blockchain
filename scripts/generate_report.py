"""
Generate Research Paper Report
Creates comprehensive report with tables, statistics, and analysis
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

def generate_html_report(benchmark_data):
    """Generate HTML report for research paper"""
    results = benchmark_data.get('results', [])
    
    # Get values for formatting
    date = benchmark_data.get('benchmark_date', 'Unknown')
    count = benchmark_data.get('total_algorithms', 0)
    iterations = results[0].get('iterations', 0) if results else 0
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>PQC Signature Algorithm Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Post-Quantum Cryptography Signature Algorithm Benchmark Report</h1>
    <div class="summary">
        <p><strong>Report Date:</strong> {date}</p>
        <p><strong>Algorithms Tested:</strong> {count}</p>
        <p><strong>Iterations per Operation:</strong> {iterations}</p>
    </div>
    
    <h2>Performance Summary</h2>
    <table>
        <tr>
            <th>Algorithm</th>
            <th>Keygen (ms)</th>
            <th>Sign (ms)</th>
            <th>Verify (ms)</th>
            <th>PubKey (B)</th>
            <th>Sig (B)</th>
        </tr>
""".format(
        date=date,
        count=count,
        iterations=iterations
    )
    
    for result in results:
        algo = result.get('algorithm', 'unknown')
        keygen = result.get('key_generation', {})
        signing = result.get('signing', {})
        verify = result.get('verification', {})
        
        keygen_mean = keygen.get('mean', 0) * 1000 if keygen else 0
        sign_mean = signing.get('mean', 0) * 1000 if signing else 0
        verify_mean = verify.get('mean', 0) * 1000 if verify else 0
        pubkey_size = keygen.get('public_key_size', 0) if keygen else 0
        sig_size = signing.get('signature_size', 0) if signing else 0
        
        html += f"""
        <tr>
            <td>{algo}</td>
            <td>{keygen_mean:.2f}</td>
            <td>{sign_mean:.2f}</td>
            <td>{verify_mean:.2f}</td>
            <td>{pubkey_size}</td>
            <td>{sig_size}</td>
        </tr>
"""
    
    html += """
    </table>
    
    <h2>Statistical Analysis</h2>
    <p>Detailed statistics available in JSON benchmark file.</p>
    
    <h2>Recommendations</h2>
    <ul>
        <li>For high-speed applications: Consider fastest algorithms</li>
        <li>For storage-constrained: Consider smallest key/signature sizes</li>
        <li>For blockchain: Consider gas-efficient options</li>
        <li>For security: Use NIST Level 3+ algorithms</li>
    </ul>
    
</body>
</html>
"""
    
    report_file = os.path.join(RESULTS_DIR, "report.html")
    with open(report_file, 'w') as f:
        f.write(html)
    
    print(f"[OK] HTML report saved to: {report_file}")
    return report_file

def main():
    """Main report generation function"""
    print("="*70)
    print("  RESEARCH PAPER REPORT GENERATOR")
    print("="*70)
    print()
    
    benchmark_data = load_latest_benchmark()
    if not benchmark_data:
        print("[ERROR] No benchmark data found")
        print("        Run: python scripts/benchmark.py first")
        sys.exit(1)
    
    print(f"[OK] Loaded benchmark data")
    print()
    
    # Generate HTML report
    html_file = generate_html_report(benchmark_data)
    
    print("\n" + "="*70)
    print("[SUCCESS] Report generation completed!")
    print(f"HTML Report: {html_file}")
    print("="*70)

if __name__ == "__main__":
    main()

