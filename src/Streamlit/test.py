import os
from pathlib import Path

src = f"{Path(__file__).resolve().parents[1]}/src"

os.sys.path.append(src)
from esynergy_open_rag.config import chain

print(chain.invoke("summary of the datamesh project"))
