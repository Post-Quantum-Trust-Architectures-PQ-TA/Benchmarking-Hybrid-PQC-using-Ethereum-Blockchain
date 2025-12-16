"""
Utility functions for contract interaction
Helper module for storing and loading contract address and ABI
"""
import os
import json

CONTRACT_INFO_FILE = os.path.join(os.path.dirname(__file__), "..", "contracts", "contract_info.json")

def save_contract_info(contract_address, abi):
    """
    Save contract address and ABI to a JSON file
    
    Args:
        contract_address: The deployed contract address
        abi: The contract ABI (list)
    """
    contract_info = {
        "address": contract_address,
        "abi": abi
    }
    
    with open(CONTRACT_INFO_FILE, "w") as f:
        json.dump(contract_info, f, indent=2)
    
    print(f"Contract info saved to {CONTRACT_INFO_FILE}")

def load_contract_info():
    """
    Load contract address and ABI from JSON file
    
    Returns:
        tuple: (contract_address, abi) or (None, None) if file doesn't exist
    """
    if not os.path.exists(CONTRACT_INFO_FILE):
        return None, None
    
    with open(CONTRACT_INFO_FILE, "r") as f:
        contract_info = json.load(f)
    
    return contract_info["address"], contract_info["abi"]

def get_contract_info_path():
    """Get the path to the contract info file"""
    return CONTRACT_INFO_FILE

