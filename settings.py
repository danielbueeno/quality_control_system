import os

# =========================
# Parâmetros de qualidade
# =========================
MIN_WEIGHT = 95
MAX_WEIGHT = 105
MIN_LENGTH = 10
MAX_LENGTH = 20
ALLOWED_COLORS = {"azul", "verde"}

# Capacidade da caixa (evita "número mágico" espalhado no código)
BOX_CAPACITY = 10

# =========================
# Diretórios / Ficheiros
# =========================
DATA_DIR = "data"
BOX_DIR = os.path.join(DATA_DIR, "boxes")
REPORT_DIR = os.path.join(DATA_DIR, "reports")
REJECTS_FILE = os.path.join(DATA_DIR, "reprovadas.json")
