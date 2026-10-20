import os
import sys
import time
import webbrowser
import threading
from pathlib import Path

# 1. Descobrir a pasta base (onde está o .exe ou onde corre o dev)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent

# 2. Criar a pasta data/ e o ficheiro de log
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
( DATA_DIR / "uploads" ).mkdir(parents=True, exist_ok=True)
( DATA_DIR / "uploads" / "logotipos" ).mkdir(parents=True, exist_ok=True)

# 3. Redirecionar stdout/stderr para o ficheiro de log
_log_file = DATA_DIR / "server.log"
_log_f = open(_log_file, "a", encoding="utf-8", buffering=1)
sys.stdout = _log_f
sys.stderr = _log_f

# 4. Importar o uvicorn SÓ DEPOIS de redirecionar o output
import uvicorn

HOSTS_FILE = Path(os.environ.get("WINDIR", r"C:\Windows")) / "System32" / "drivers" / "etc" / "hosts"
DOMINIO = "sge-faturacao"
PORTA = 8000


def configurar_hosts() -> bool:
    try:
        if not HOSTS_FILE.exists():
            return False
        conteudo = HOSTS_FILE.read_text(encoding="utf-8", errors="ignore")
        if DOMINIO in conteudo:
            return True
        with open(HOSTS_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n127.0.0.1 {DOMINIO}\n")
        return True
    except Exception:
        return False


def abrir_browser(url: str):
    time.sleep(2)
    webbrowser.open(url)


if __name__ == "__main__":
    print("=====================================")
    print("   SGE - Sistema de Gestão Empresarial")
    print("=====================================")

    hosts_ok = configurar_hosts()

    if hosts_ok:
        url_inicial = f"http://{DOMINIO}:{PORTA}"
    else:
        url_inicial = f"http://localhost:{PORTA}"

    threading.Thread(target=abrir_browser, args=(url_inicial,), daemon=True).start()
    
    # 5. Correr o servidor
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORTA, log_level="critical")