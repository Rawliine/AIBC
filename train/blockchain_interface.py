import json
from web3 import Web3

class BlockchainInterface:
    def __init__(self, rpc_url="http://localhost:8545", contract_address=None):
        """Interface pour interagir avec les smart contracts Ethereum"""
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract_address = contract_address
        self.contract = None
        
        # Charger l'ABI du contrat
        if contract_address:
            with open('contracts/RewardDistribution.json', 'r') as f:
                contract_json = json.load(f)
                self.contract = self.w3.eth.contract(
                    address=contract_address,
                    abi=contract_json['abi']
                )
    
    def record_contribution(self, worker_address, contribution_score, epoch):
        """Enregistre la contribution d'un worker sur la blockchain"""
        if not self.contract:
            raise ValueError("Contract not initialized")
            
        # Compte admin pour transactions
        admin = self.w3.eth.accounts[0]
        
        # Exécuter la transaction
        tx_hash = self.contract.functions.recordContribution(
            worker_address,
            int(contribution_score * 100),  # Convertir en entier
            epoch
        ).transact({'from': admin})
        
        # Attendre confirmation
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return receipt 