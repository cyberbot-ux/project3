from dataclasses import dataclass

@dataclass
class CardTransaction:
    batch_date: str
    card_type: str
    quantity: int
    gross: float
    net: float
    fee: float
