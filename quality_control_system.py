
from __future__ import annotations
from typing import Dict, List, Tuple
import os
import json
from datetime import datetime
from models import Item, Box
from settings import (MIN_WEIGHT,MAX_WEIGHT, REPORT_DIR, MIN_LENGTH, MAX_LENGTH, ALLOWED_COLORS, BOX_DIR, REPORT_DIR, DATA_DIR, REJECTS_FILE)

# =========================
# Estado em memória
# =========================
items: Dict[str, Item] = {} # Dicionário de todas as peças (aprovadas e reprovadas) indexadas por ID.

# Índices auxiliares para impressão e contagem rápidas.
approved_items_ids: List[str] = []
not_approved_items_ids: List[str] = []

closed_boxes: List[Box] = [] # Listas com o histórico de caixas.
open_box: Box | None = None  # definido durante load_state()

def _ensure_dirs() -> None:
    """
    Garante que a estrutura de diretórios exista antes de ler/escrever ficheiros.
    É idempotente (pode ser chamado várias vezes sem efeitos colaterais).
    """
    os.makedirs(BOX_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

# =========================
# Funções de Persistência
# =========================
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


# =========================
# Regras de negócio (funções de uso da app)
# =========================
def list_items() -> None:
    """
    Imprime duas listas: aprovadas e reprovadas (com motivos).
    Utiliza os índices approved_items_ids e not_approved_items_ids para garantir
    ordem estável e acessos O(1) ao dicionário principal 'items'.
    """
    print("\n=== Peças Aprovadas ===")
    if not approved_items_ids:
        print("Nenhuma peça foi aprovada.")
    else:
        for pid in approved_items_ids:
            item = items[pid]
            print(f"- {item.id} | {item.weight}g | {item.color} | {item.length}cm | APROVADA")

    print("\n=== Peças Reprovadas ===")
    if not not_approved_items_ids:
        print("Nenhuma peça foi reprovada.")
    else:
        for pid in not_approved_items_ids:
            item = items[pid]
            print(f"- {item.id} | {item.weight}g | {item.color} | {item.length}cm | REPROVADA ({'; '.join(item.failure_reasons)})")

def store_item(item: Item) -> None:
    """
    Coloca a peça aprovada na caixa aberta. Se a caixa encher:
      - marca como 'closed'
      - salva a caixa no disco
      - cria e salva uma nova caixa aberta (id sequencial)
    Caso contrário, apenas salva o progresso da caixa aberta atual.
    """
    global open_box, closed_boxes

    open_box.items.append(item)
    if open_box.full():
        open_box.closed = True
        save_box(open_box)
        closed_boxes.append(open_box)
        # abre nova
        open_box = Box(id=open_box.id + 1, closed=False, items=[])
        save_box(open_box)
    else:
        # Apenas salva progresso da caixa aberta
        save_box(open_box)

def evaluate_item(item: Item) -> None:
    """
    Aplica as regras de qualidade à peça e define:
      - item.approved (True/False)
      - item.failure_reasons (lista de strings em caso de reprovação)
    """
    reasons = []
    if not (MIN_WEIGHT <= item.weight <= MAX_WEIGHT):
        reasons.append("Peso fora da faixa")
    if item.color not in ALLOWED_COLORS:
        reasons.append("Cor inválida")
    if not (MIN_LENGTH <= item.length <= MAX_LENGTH):
        reasons.append("Comprimento fora da faixa")

    if reasons:
        item.approved = False
        item.failure_reasons = reasons
    else:
        item.approved = True
        item.failure_reasons = []

def register_item() -> None:
    """
    Fluxo interativo de cadastro:
      - Lê dados da peça (com validações básicas de entrada)
      - Avalia qualidade
      - Persiste conforme aprovada/reprovada
    """
    print("\n=== Cadastro de nova peça ===")
    id = input("ID da peça: ").strip()
    if not id:
        print("ID não pode ser vazio.")
        return
    if id in items:
        print(f"ERRO: Já existe uma peça com ID '{id}'.")
        return

    try:
        weight = float(input("Peso (g): ").replace(",", "."))
        color = input("Cor (azul/verde): ").strip()
        length = float(input("Comprimento (cm): ").replace(",", "."))
    except ValueError:
        print("Entrada inválida. Use números para peso e comprimento.")
        return

    item = Item(id, weight, color, length)
    evaluate_item(item)
    items[id] = item

    if item.approved:
        approved_items_ids.append(id)
        store_item(item)
        print(f"Peça {id} APROVADA e alocada na caixa aberta.")
    else:
        not_approved_items_ids.append(id)
        save_rejects()
        print(f"Peça {id} REPROVADA. Motivos: {', '.join(item.failure_reasons)}")

def remove_item() -> None:
    """
    Remove uma peça do sistema, incluindo sua presença em caixa, se for aprovada.
    Regras:
      - Se estava numa caixa fechada, a caixa continua fechada (não muda o estado 'closed').
      - Atualiza os ficheiros correspondentes (caixa ou reprovadas.json).
    """
    global closed_boxes, open_box
    print("\n=== Remoção de peça ===")
    id = input("Informe o ID da peça a remover: ").strip()
    if id not in items:
        print(f"Peça '{id}' não encontrada.")
        return

    item = items[id]

    # Se aprovada, tentar removê-la da caixa (aberta ou fechada)
    if item.approved:
        # Tenta na caixa aberta
        if item in open_box.items:
            open_box.items.remove(item)
            save_box(open_box)
        else:
            # Procura nas caixas fechadas
            for closed_box in closed_boxes:
                if item in closed_box.items:
                    closed_box.items.remove(item)
                    # permanece fechada mesmo com menos de 10
                    save_box(closed_box)
                    break

        # Remove do índice de aprovadas
        if id in approved_items_ids:
            approved_items_ids.remove(id)
    else:
        # Remove do índice de reprovadas
        if id in not_approved_items_ids:
            not_approved_items_ids.remove(id)
            save_rejects()

    # Por fim, remove do dicionário principal
    del items[id]
    print(f"Peça '{id}' removida com sucesso.")

def list_closed_boxes() -> None:
    """
    Imprime o inventário das caixas fechadas.
    Útil para auditoria e para verificar a distribuição de itens por caixa.
    """
    print("\n=== Caixas Fechadas ===")
    if not closed_boxes:
        print("Não há caixas fechadas")
        return
    for box in closed_boxes:
        print(f"- Caixa #{box.id}: {len(box.items)} peça(s) (fechada)")
        for item in box.items:
            print(f"  • {item.id} ({item.weight}g, {item.color}, {item.length}cm)")

def generate_final_report() -> None:
    """
    Gera e exibe o relatório final no terminal e grava um snapshot em ficheiro .txt.
    O relatório inclui:
      - Totais de aprovadas e reprovadas
      - Contagem por motivo de reprovação
      - Número de caixas fechadas
      - Estado resumido da caixa aberta
    """
    lines: List[str] = []
    lines.append("=== Relatório Final ===")
    total_aproved = len(approved_items_ids)
    total_not_approved = len(not_approved_items_ids)
    total_boxes = len(closed_boxes)

    lines.append(f"Total de peças aprovadas: {total_aproved}")
    lines.append(f"Total de peças reprovadas: {total_not_approved}")

    if total_not_approved:
        lines.append("\nMotivos de reprovação:")
        failure_reasons: Dict[str, int] = {}
        for id in not_approved_items_ids:
            item = items[id]
            for reason in item.failure_reasons:
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        for reason, q in failure_reasons.items():
            lines.append(f"- {reason}: {q}")

    lines.append(f"\nQuantidade de caixas utilizadas (fechadas): {total_boxes}")

    # Status da caixa aberta
    lines.append(f"Peças atualmente na caixa aberta (#{open_box.id}): {len(open_box.items)}")
    if open_box.items:
        ids = ', '.join(item.id for item in open_box.items)
        lines.append(f"IDs: {ids}")

    report_text = "\n".join(lines)

    # Exibir na tela
    print("\n" + report_text)

    # Salvar no ficheiro
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(REPORT_DIR, f"relatorio_{ts}.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text + "\n")
    print(f"\nRelatório salvo em: {report_path}")

def show_menu() -> None:
    """Menu simples de opções para interação no terminal."""
    print("\n" + "=" * 48)
    print(" SISTEMA DE QUALIDADE E EMBALAGEM DE PEÇAS ")
    print("=" * 48)
    print("1. Cadastrar nova peça")
    print("2. Listar peças aprovadas/reprovadas")
    print("3. Remover peça cadastrada")
    print("4. Listar caixas fechadas")
    print("5. Gerar relatório final")
    print("0. Sair")

def main():
    """
    Ponto de entrada da aplicação:
      - Garante diretórios
      - Carrega estado persistido
      - Loop principal do menu
    """
    _ensure_dirs()
    load_state()
    while True:
        show_menu()
        option = input("Escolha uma opção: ").strip()

        if option == "1":
            register_item()
        elif option == "2":
            list_items()
        elif option == "3":
            remove_item()
        elif option == "4":
            list_closed_boxes()
        elif option == "5":
            generate_final_report()
        elif option == "0":
            print("Encerrando...")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main()
