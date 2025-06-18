# program_manager.py
from xml_parser import parse_single_file
from card_transaction import CardTransaction
import os

transaction_cache = {}

def load_files(xml_files):
    """ Load multiple XML files into the transaction cache. """
    transaction_cache.clear()
    for path in xml_files:
        filename = os.path.basename(path)
        transactions = parse_single_file(path)
        transaction_cache[filename] = transactions
def add_file_to_cache(xml_file):
    abs_path = os.path.join(os.path.dirname(__file__), xml_file) if not os.path.isabs(xml_file) else xml_file
    filename = os.path.basename(abs_path)
    if filename not in transaction_cache:
        transaction_cache[filename] = parse_single_file(abs_path)

def get_transactions(file_name):
    if file_name == "All Files":
        all_tx = []
        for tx_list in transaction_cache.values():
            all_tx.extend(tx_list)
        return all_tx
    return transaction_cache.get(file_name, [])
