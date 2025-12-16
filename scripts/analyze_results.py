"""
Results Analysis Tool
Analyzes collected metrics and generates reports
"""
import os
import sys
import csv
import json
from datetime import datetime

# Get project root and change to it
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

RESULTS_FILE = os.path.join(PROJECT_ROOT, "data", "results.csv")

def load_results():
    """
    Load results from CSV file
    """
    print("Loading results from CSV...")
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            reader = csv.DictReader(f)
            results = list(reader)
    return results

def analyze_by_algorithm(results):
    """
    Analyze results grouped by algorithm
    """
    print("Analyzing results by algorithm...")
    algorithms = {}
    for result in results:
        algo = result.get('algorithm', 'unknown')
        if algo not in algorithms:
            algorithms[algo] = []
        algorithms[algo].append(result)
    
    # Calculate statistics for each algorithm
    analysis = {}
    for algo, algo_results in algorithms.items():
        analysis[algo] = {
            'count': len(algo_results),
        }
    return analysis

def generate_report(analysis):
    """
    Generate analysis report
    """
    print("Generating report...")
    report = {
        'timestamp': datetime.now().isoformat(),
        'by_algorithm': analysis,
    }
    
    # Save to file
    report_file = os.path.join(PROJECT_ROOT, "data", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """Main analysis function"""
    print("=" * 70)
    print("  RESULTS ANALYSIS TOOL")
    print("=" * 70)
    print()
    print("This tool will:")
    print("  1. Load results from CSV")
    print("  2. Analyze by algorithm")
    print("  3. Calculate statistics")
    print("  4. Generate comparison reports")
    print("  5. Export analysis results")
    print()
    
    results = load_results()
    if not results:
        print("No results found. Run benchmarks first.")
        return
    
    analysis = analyze_by_algorithm(results)
    report = generate_report(analysis)
    
    if report:
        print(f"\n[SUCCESS] Report generated: {report.get('timestamp', 'N/A')}")

if __name__ == "__main__":
    main()

