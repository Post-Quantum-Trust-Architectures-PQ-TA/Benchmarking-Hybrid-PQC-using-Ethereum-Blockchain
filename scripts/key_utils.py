"""
Utility functions for PQC key management
Helper module for storing and loading PQC keypairs
"""
import os
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(PROJECT_ROOT, "data", "keys")
KEYS_INFO_FILE = os.path.join(KEYS_DIR, "keys_info.json")

def ensure_keys_directory():
    """Ensure the keys directory exists"""
    os.makedirs(KEYS_DIR, exist_ok=True)

def save_key_info(account_address, algorithm, public_key_path, private_key_path):
    """
    Save key information to JSON file
    
    Args:
        account_address: Ethereum account address
        algorithm: PQC algorithm name
        public_key_path: Path to public key file
        private_key_path: Path to private key file
    """
    ensure_keys_directory()
    
    # Load existing info or create new
    if os.path.exists(KEYS_INFO_FILE):
        with open(KEYS_INFO_FILE, "r") as f:
            keys_info = json.load(f)
    else:
        keys_info = {}
    
    # Update info for this account
    if account_address not in keys_info:
        keys_info[account_address] = {}
    
    keys_info[account_address][algorithm] = {
        "public_key_path": public_key_path,
        "private_key_path": private_key_path
    }
    
    # Save updated info
    with open(KEYS_INFO_FILE, "w") as f:
        json.dump(keys_info, f, indent=2)

def load_key_info(account_address, algorithm=None):
    """
    Load key information for an account
    
    Args:
        account_address: Ethereum account address
        algorithm: PQC algorithm name (optional, returns all if not specified)
    
    Returns:
        dict: Key information or None if not found
    """
    if not os.path.exists(KEYS_INFO_FILE):
        return None
    
    with open(KEYS_INFO_FILE, "r") as f:
        keys_info = json.load(f)
    
    if account_address not in keys_info:
        return None
    
    if algorithm:
        return keys_info[account_address].get(algorithm)
    else:
        return keys_info[account_address]

def load_keypair(account_address, algorithm):
    """
    Load keypair from files
    
    Args:
        account_address: Ethereum account address
        algorithm: PQC algorithm name
    
    Returns:
        tuple: (public_key_bytes, private_key_bytes) or (None, None) if not found
    """
    key_info = load_key_info(account_address, algorithm)
    if not key_info:
        return None, None
    
    try:
        with open(key_info["public_key_path"], "rb") as f:
            public_key = f.read()
        
        with open(key_info["private_key_path"], "rb") as f:
            private_key = f.read()
        
        return public_key, private_key
    except Exception:
        return None, None

def get_key_paths(account_address, algorithm):
    """
    Get file paths for keys
    
    Args:
        account_address: Ethereum account address
        algorithm: PQC algorithm name
    
    Returns:
        tuple: (public_key_path, private_key_path)
    """
    ensure_keys_directory()
    account_short = account_address[:10].replace("0x", "")
    pubkey_file = os.path.join(KEYS_DIR, f"{account_short}_pubkey_{algorithm}.bin")
    privkey_file = os.path.join(KEYS_DIR, f"{account_short}_privkey_{algorithm}.bin")
    return pubkey_file, privkey_file

