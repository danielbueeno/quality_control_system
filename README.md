# Gestão de Peças, Qualidade e Armazenamento

Aplicação de terminal para **avaliar peças**, **armazená-las em caixas** (até 10 por caixa) e **persistir tudo em ficheiros**.  
Ao iniciar, o sistema **reconstrói o estado** a partir dos ficheiros; ao operar, **salva** as alterações (caixas, reprovadas e relatórios).

---

## 📁 Estrutura do projeto

- settings.py — Configurações (faixas de qualidade, paths, capacidade da caixa)
- models.py — Entidades de domínio: Item e Box
- quality_control_system.py — Programa principal (CLI)

- data/ — Criado automaticamente
  - boxes/ — Caixas salvas como JSON (box_0001.json, etc.)
  - reports/ — Relatórios gerados (.txt)
  - reprovadas.json — Lista de peças reprovadas

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

 ``python3 quality_control_system.py``

### Use o menu interativo no terminal:

<img width="351" height="304" alt="Screenshot 2025-10-26 at 15 49 48" src="https://github.com/user-attachments/assets/88414e0f-33cf-4e88-8c75-a62598110b97" />

### Acesse os dados quando quiser na caixa criada

<img width="369" height="317" alt="Screenshot 2025-10-26 at 15 52 22" src="https://github.com/user-attachments/assets/231deb91-6f2a-48ea-a046-2a2b3529820b" />



