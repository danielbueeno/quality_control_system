# Sistema de Qualidade e Embalagem de Peças (persistente)

Aplicação de terminal para **avaliar peças**, **armazená-las em caixas** (até 10 por caixa) e **persistir tudo em ficheiros**.  
Ao iniciar, o sistema **reconstrói o estado** a partir dos ficheiros; ao operar, **salva** as alterações (caixas, reprovadas e relatórios).

---

## 📁 Estrutura do projeto

├─ settings.py # Configurações (faixas de qualidade, paths, capacidade da caixa)
├─ models.py # Entidades de domínio: Item e Box
├─ persistence.py # Funções de IO em disco (caixas, reprovadas, relatórios/dirs)
├─ quality_control_system.py# Programa principal (CLI)
└─ data/ # Criado automaticamente
├─ boxes/ # Caixas salvas como JSON (box_0001.json, etc.)
├─ reports/ # Relatórios gerados (.txt)
└─ reprovadas.json # Lista de peças reprovadas

---

## 🧠 Como funciona

- **Avaliação de qualidade**  
  Regras em `settings.py`:

  - Peso entre `MIN_WEIGHT` e `MAX_WEIGHT` (g)
  - Comprimento entre `MIN_LENGTH` e `MAX_LENGTH` (cm)
  - Cores permitidas em `ALLOWED_COLORS` (ex.: `"azul"`, `"verde"`)

- **Armazenamento em caixas**  
  Capacidade definida por `BOX_CAPACITY` (padrão **10**).  
  Quando a caixa aberta atinge a capacidade, ela é **fechada** e é criada automaticamente a **próxima**.

- **Persistência**

  - Caixas: `data/boxes/box_XXXX.json`
  - Reprovadas: `data/reprovadas.json`
  - Relatórios: `data/reports/relatorio_YYYYMMDD_HHMMSS.txt`

- **Reinício do app**  
  Ao iniciar, o app **lê** as caixas e reprovadas para reconstruir:
  - `items` (todas as peças)
  - `approved_items_ids` / `not_approved_items_ids`
  - `closed_boxes` e `open_box`

---

## ▶️ Como rodar (passo a passo)

> Requisitos: **Python 3** Não há dependências externas.

# macOS / Linux

python3 quality_control_system.py

# Windows

python quality_control_system.py

### Use o menu interativo no terminal:

================================
SISTEMA DE QUALIDADE E EMBALAGEM DE PEÇAS
================================

1. Cadastrar nova peça
2. Listar peças aprovadas/reprovadas
3. Remover peça cadastrada
4. Listar caixas fechadas
5. Gerar relatório final
6. Sair

## ⌨️ Exemplos de entradas e saídas
# quality_control_system
