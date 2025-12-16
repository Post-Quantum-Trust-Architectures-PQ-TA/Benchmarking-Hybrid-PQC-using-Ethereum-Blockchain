# Hybrid PQC-Ethereum Signature Project

A comprehensive research project evaluating Post-Quantum Cryptography (PQC) algorithms for Ethereum blockchain integration. This project benchmarks 7 NIST-standardized PQC signature schemes against ECDSA baseline, measuring performance, gas costs, and scalability.

## Project Overview

This project implements and benchmarks hybrid digital signatures combining Post-Quantum Cryptography with Ethereum's native ECDSA signatures. It provides a complete benchmarking suite for research paper publication, including:

- **7 PQC Algorithms**: Dilithium2/3/5, SPHINCS+ (2 variants), FALCON-512/1024
- **Comprehensive Benchmarks**: Key generation, signing, verification, gas costs
- **Scalability Analysis**: Batch operations testing (1 to 2048 operations)
- **Visualization**: Publication-ready charts and graphs
- **Research Tools**: LaTeX tables, CSV exports, statistical analysis

## Installation

### Prerequisites

- Python 3.10 or higher
- Ganache (local Ethereum blockchain) - [Download](https://trufflesuite.com/ganache/)

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:**
- `web3` - Ethereum blockchain interaction
- `py-solc-x` - Solidity contract compilation
- `quantcrypt` - PQC algorithm implementations
- `cryptography` - ECDSA baseline
- `matplotlib`, `numpy` - Visualization and analysis
- `tqdm` - Progress bars

## Quick Start

### 1. Start Ganache

Launch Ganache and ensure it's running on `http://127.0.0.1:8545`

### 2. Deploy Contract

```bash
python scripts/deploy.py
```

### 3. Run Benchmarks

```bash
# Run comprehensive benchmarks (recommended: 30 iterations)
python scripts/benchmark.py --iterations 30

# Skip gas benchmarking (faster)
python scripts/benchmark.py --iterations 30 --skip-gas

# Test specific algorithms
python scripts/benchmark.py --algorithms dilithium3 falcon512 --iterations 20
```

### 4. Generate Results and Visualizations

```bash
# Generate all charts and figures
python scripts/visualize_results.py

# Generate algorithm comparison tables
python scripts/compare_algorithms.py

# Generate HTML report
python scripts/generate_report.py
```

### 5. Batch Scalability Testing (Optional)

```bash
# Test scalability with batch operations
python scripts/batch_operations.py --algorithm dilithium3

# Analyze batch scalability results
python scripts/analyze_batch_scalability.py
```

## Output Files

### Benchmark Results
- **JSON**: `data/benchmarks/benchmark_YYYYMMDD_HHMMSS.json` - Complete benchmark data
- **CSV**: `data/benchmarks/comparison_matrix.csv` - Algorithm comparison matrix
- **LaTeX**: `data/benchmarks/comparison_table.tex` - Publication-ready table

### Visualizations
- **Performance Comparison**: `data/figures/performance_comparison.png`
- **Size Comparison**: `data/figures/size_comparison.png`
- **Gas Cost Comparison**: `data/figures/gas_cost_comparison.png`
- **PQC vs ECDSA**: `data/figures/pqc_vs_ecdsa.png`
- **Scalability Charts**: `data/figures/scalability_*.png`

### Reports
- **HTML Report**: `data/benchmarks/report.html` - Interactive benchmark report

## Project Structure

```
pqc_proj/
├── contracts/
│   ├── KeyRegistry.sol          # Smart contract for PQC key registration
│   └── contract_info.json       # Deployed contract address and ABI
├── scripts/
│   ├── deploy.py                 # Deploy contract to Ganache
│   ├── benchmark.py             # Comprehensive benchmarking suite
│   ├── visualize_results.py    # Generate charts and figures
│   ├── compare_algorithms.py   # Algorithm comparison analysis
│   ├── batch_operations.py      # Scalability testing
│   ├── analyze_batch_scalability.py  # Batch analysis
│   └── [other utility scripts]
├── data/
│   ├── benchmarks/              # Benchmark results (JSON, CSV, LaTeX)
│   ├── figures/                 # Generated charts and visualizations
│   └── keys/                     # Generated PQC keypairs
├── tests/
│   └── test_hybrid.py           # Unit tests
└── requirements.txt              # Python dependencies
```

## Supported Algorithms

### ML-DSA (CRYSTALS-Dilithium)
- **Dilithium2** (ML-DSA-44) - NIST Security Level 2
- **Dilithium3** (ML-DSA-65) - NIST Security Level 3
- **Dilithium5** (ML-DSA-87) - NIST Security Level 5

### SLH-DSA (SPHINCS+)
- **SPHINCS+ Small** (sphincs128f) - NIST Security Level 1
- **SPHINCS+ Fast** (sphincs_fast) - NIST Security Level 3/5

### FALCON
- **FALCON-512** - NIST Security Level 1
- **FALCON-1024** - NIST Security Level 5

## Metrics Collected

- **Performance**: Key generation, signing, and verification times
- **Sizes**: Public key and signature sizes (bytes)
- **Gas Costs**: Registration and transaction gas usage
- **Scalability**: Throughput at different batch sizes
- **Statistical Analysis**: Mean, median, standard deviation, min/max

## Usage Examples

### Basic Benchmarking
```bash
# Run all algorithms with 30 iterations
python scripts/benchmark.py --iterations 30

# Test specific algorithms only
python scripts/benchmark.py --algorithms dilithium3 falcon512 --iterations 20

# Skip gas benchmarking (faster)
python scripts/benchmark.py --iterations 30 --skip-gas
```

### Visualization
```bash
# Generate all charts from latest benchmark
python scripts/visualize_results.py

# Generate charts from specific benchmark file
python scripts/visualize_results.py --benchmark-file data/benchmarks/benchmark_20251215_223916.json
```

### Analysis
```bash
# Generate comparison tables and insights
python scripts/compare_algorithms.py

# Generate HTML report
python scripts/generate_report.py
```

### Scalability Testing
```bash
# Test batch operations for specific algorithm
python scripts/batch_operations.py --algorithm dilithium3

# Test with parallel processing
python scripts/batch_operations.py --algorithm dilithium3 --parallel

# Analyze batch results
python scripts/analyze_batch_scalability.py
```

## Notes

- **Ganache Required**: All blockchain operations require a running Ganache instance
- **Gas Costs**: Gas benchmarking requires contract deployment and consumes test ETH
- **Performance**: Benchmarking can take 10-30 minutes depending on iterations
- **Results**: All results are saved automatically with timestamps

## License

MIT

## References

- [NIST PQC Standards](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [Ethereum Documentation](https://ethereum.org/en/developers/)
- [QuantCrypt Library](https://pypi.org/project/quantcrypt/)
