from typing import List
from settings import BOX_CAPACITY

class Item:
    """
    Representa uma peça.

    Atributos:
        id: identificador único no sistema (string).
        weight: peso em gramas (float).
        color: cor normalizada para minúsculas (string).
        length: comprimento em centímetros (float).
        approved: True se aprovada, False se reprovada.
        failure_reasons: lista de motivos de reprovação (strings).
    """
    def __init__(self, id: str, weight: float, color: str, length: float, approved: bool=False, failure_reasons: List[str]|None=None):
        self.id = id
        self.weight = weight
        self.color = color.lower().strip()
        self.length = length
        self.approved = approved
        self.failure_reasons: List[str] = failure_reasons or []

    def __repr__(self):
        status = "APROVADA" if self.approved else f"REPROVADA ({'; '.join(self.failure_reasons)})"
        return f"Peca(id={self.id}, peso={self.weight}g, cor={self.color}, comp={self.length}cm, {status})"

    def to_dict(self) -> dict:
        """Serializa a peça para dicionário (adequado para json.dump)."""
        return {
            "id": self.id,
            "weight": self.weight,
            "color": self.color,
            "length": self.length,
            "approved": self.approved,
            "failure_reasons": list(self.failure_reasons),
        }

    @staticmethod
    def from_dict(d: dict) -> "Item":
        """Desserializa uma peça a partir de um dicionário (json.load)."""
        return Item(
            id=d["id"],
            weight=d["weight"],
            color=d["color"],
            length=d["length"],
            approved=d.get("approved", False),
            failure_reasons=d.get("failure_reasons", []),
        )

class Box:
    """
    Representa uma caixa (aberta ou fechada).

    Regras:
      - Uma caixa é considerada "cheia" quando contém BOX_CAPACITY itens.
      - Caixas fechadas não são reabertas, mesmo se algum item for removido.
    """
    def __init__(self, id: int, closed: bool=False, items: List[Item]|None=None):
        self.id = id
        self.closed = closed
        self.items: List[Item] = items or []

    def full(self) -> bool:
        """
        Retorna True se a caixa atingiu a capacidade máxima (BOX_CAPACITY).
        Esta função centraliza a regra de "10 peças por caixa".
        """
        return len(self.items) >= BOX_CAPACITY

    def __repr__(self):
        status = "fechada" if self.closed else "aberta"
        return f"Caixa #{self.id} ({status}, pecas={len(self.items)})"

    def to_dict(self) -> dict:
        """Serializa a caixa (incluindo os itens) para JSON."""
        return {
            "id": self.id,
            "closed": self.closed,
            "items": [it.to_dict() for it in self.items],
        }

    @staticmethod
    def from_dict(d: dict) -> "Box":
        """
        Desserializa uma caixa a partir de dicionário.
        Converte itens internos usando Item.from_dict.
        """
        return Box(
            id=int(d["id"]),
            closed=bool(d.get("closed", False)),
            items=[Item.from_dict(x) for x in d.get("items", [])],
        )