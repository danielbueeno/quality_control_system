import os
from typing import List, Tuple
import json
from models import Item, Box
from settings import BOX_DIR, REPORT_DIR, DATA_DIR, REJECTS_FILE

def _ensure_dirs() -> None:
    """
    Garante que a estrutura de diretórios exista antes de ler/escrever ficheiros.
    É idempotente (pode ser chamado várias vezes sem efeitos colaterais).
    """
    os.makedirs(BOX_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def _box_filename(box_id: int) -> str:
    """
    Gera o caminho do ficheiro JSON de uma caixa.
    Ex.: box_id=1 -> data/boxes/box_0001.json
    """
    return os.path.join(BOX_DIR, f"box_{box_id:04d}.json")

def save_box(box: Box) -> None:
    """Grava o estado atual de uma caixa em disco (formato JSON)."""
    _ensure_dirs()
    with open(_box_filename(box.id), "w", encoding="utf-8") as f:
        json.dump(box.to_dict(), f, ensure_ascii=False, indent=2)

def load_boxes() -> Tuple[List[Box], Box | None]:
    """
    Lê todas as caixas do diretório BOX_DIR.
    Retorna (lista_de_caixas_fechadas, caixa_aberta).

    Estratégia:
      - Lê todos os ficheiros box_*.json válidos.
      - Se não houver nenhum, cria a primeira caixa aberta (#1).
      - A caixa aberta é a de MAIOR ID com closed == False.
      - Se não existir nenhuma aberta, cria uma nova com id = max_id + 1.
    """
    _ensure_dirs()
    boxes: List[Box] = []
    for name in sorted(os.listdir(BOX_DIR)):
        if not name.startswith("box_") or not name.endswith(".json"):
            continue
        path = os.path.join(BOX_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                boxes.append(Box.from_dict(data))
        except Exception as e:
            print(f"Aviso: não foi possível ler '{path}': {e}")

    if not boxes:
        # Nenhuma caixa no disco: criar a #1 aberta
        new_box = Box(id=1, closed=False, items=[])
        save_box(new_box)
        return [], new_box

    # A "caixa aberta" é a de maior id com closed == False; se nenhuma, cria nova
    open_candidates = [b for b in boxes if not b.closed]
    if open_candidates:
        open_b = sorted(open_candidates, key=lambda b: b.id)[-1]
    else:
        # Todas no disco estão fechadas -> abre a próxima
        next_id = max(b.id for b in boxes) + 1
        open_b = Box(id=next_id, closed=False, items=[])
        save_box(open_b)

    closed = sorted([b for b in boxes if b.closed], key=lambda b: b.id)
    return closed, open_b

def save_rejects() -> None:
    """
    Grava todas as peças reprovadas num ficheiro único (REJECTS_FILE).
    """
    _ensure_dirs()
    payload = [items[pid].to_dict() for pid in not_approved_items_ids]
    with open(REJECTS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def load_rejects() -> List[Item]:
    """
    Lê o ficheiro de reprovadas. Se não existir, retorna lista vazia.
    Em caso de erro de leitura, alerta e retorna lista vazia para não
    interromper o fluxo do programa.
    """
    _ensure_dirs()
    if not os.path.exists(REJECTS_FILE):
        return []
    try:
        with open(REJECTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Item.from_dict(d) for d in data]
    except Exception as e:
        print(f"Aviso: não foi possível ler '{REJECTS_FILE}': {e}")
        return []

def load_state() -> None:
    """
    Reconstrói TODO o estado em memória a partir dos ficheiros no disco.
    - Caixas (fechadas e aberta) => peças aprovadas.
    - reprovadas.json => peças reprovadas.
    """
    global items, approved_items_ids, not_approved_items_ids, closed_boxes, open_box

    items = {}
    approved_items_ids = []
    not_approved_items_ids = []

    closed_boxes, open_box = load_boxes()

    # Itens aprovados vêm das caixas (fechadas e aberta)
    for b in closed_boxes + ([open_box] if open_box else []):
        for it in b.items:
            items[it.id] = it
            if it.approved:
                approved_items_ids.append(it.id)

    # Itens reprovados do ficheiro
    rejects = load_rejects()
    for it in rejects:
        items[it.id] = it
        not_approved_items_ids.append(it.id)

def persist_after_removal(removed_item: Item) -> None:
    """
    Atualiza os ficheiros após remover uma peça do sistema.
    Observa a regra: caixa fechada continua fechada, mesmo com < BOX_CAPACITY itens.
    """
    global closed_boxes, open_box
    if removed_item.approved:
        # Removida de uma caixa (aberta ou fechada): atualizar o ficheiro da respectiva caixa
        # Procurar em aberta
        if removed_item in open_box.items:
            save_box(open_box)
        else:
            # Procurar qual fechada continha
            for b in closed_boxes:
                if removed_item in b.items:
                    # regra: permanece fechada mesmo com menos de 10
                    save_box(b)
                    break
    else:
        # Atualizar reprovadas.json
        save_rejects()