// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title KeyRegistry
 * @dev A simple contract to register PQC public keys and log PQC signatures
 */
contract KeyRegistry {
    // Mapping to store PQC public keys for each Ethereum address
    mapping(address => bytes) public pqPubKey;
    
    // Event emitted when a PQC signature is logged
    event PQCSignature(
        address indexed from,
        bytes signature,
        bytes message
    );
    
    // Event emitted when a PQC public key is registered
    event PQCKeyRegistered(
        address indexed user,
        bytes publicKey
    );
    
    /**
     * @dev Register a PQC public key for the caller's address
     * @param pk The PQC public key bytes to register
     */
    function registerPQCKey(bytes memory pk) public {
        pqPubKey[msg.sender] = pk;
        emit PQCKeyRegistered(msg.sender, pk);
    }
    
    /**
     * @dev Log a PQC signature and message (for off-chain verification)
     * @param signature The PQC signature bytes
     * @param message The original message that was signed
     */
    function logSignature(bytes memory signature, bytes memory message) public {
        emit PQCSignature(msg.sender, signature, message);
    }
    
    /**
     * @dev Get the registered PQC public key for an address
     * @param user The address to query
     * @return The PQC public key bytes (empty if not registered)
     */
    function getPQCKey(address user) public view returns (bytes memory) {
        return pqPubKey[user];
    }
}

