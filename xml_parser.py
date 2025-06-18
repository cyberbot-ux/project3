import os
import xml.etree.ElementTree as ET
from card_transaction import CardTransaction

cache = {}

def parse_folder(folder_path):
    all_transactions = []
    abs_folder = os.path.abspath(folder_path)

    if not os.path.isdir(abs_folder):
        print(f"Folder not found: {abs_folder}")
        return all_transactions

    for filename in os.listdir(abs_folder):
        if filename.lower().endswith('.xml'):
            file_path = os.path.join(abs_folder, filename)
            all_transactions.extend(parse_single_file(file_path))

    return all_transactions

def parse_single_file(file_path):
    abs_path = os.path.abspath(file_path)

    if abs_path in cache:
        return cache[abs_path]

    transactions = []

    if not os.path.exists(abs_path):
        print(f"File not found: {abs_path}")
        return transactions

    try:
        tree = ET.parse(abs_path)
        root = tree.getroot()

        for batch in root.findall(".//Batch"):
            date = batch.findtext("BatchDate", default="UNKNOWN")

            for card in batch.findall("CardType"):
                card_type = card.attrib.get("identType", "UNKNOWN")
                quantity = int(card.attrib.get("quantity", "0"))
                gross = float(card.attrib.get("grossAmount", "0"))
                net = float(card.attrib.get("netAmount", "0"))
                charge = card.find(".//ChargeAmt")
                fee = float(charge.text) if charge is not None else 0.0

                transactions.append(CardTransaction(
                    batch_date=date,
                    card_type=card_type,
                    quantity=quantity,
                    gross=gross,
                    net=net,
                    fee=fee
                ))

    except Exception as e:
        print(f"Error parsing {abs_path}: {e}")

    cache[abs_path] = transactions
    return transactions

    
    
def clear_cache():
    global cache
    cache = {}
    print("Cache cleared.")