"""Indexa los fragmentos en una base vectorial local (Chroma).

Uso:  python indexar.py fragmentos.jsonl indice

Lee el .jsonl que produce extraer.py, calcula el embedding de cada fragmento
con el modelo servido por Ollama y lo guarda en disco junto con su documento
y su pagina. Es el paso que permite buscar por significado y no por palabras.
"""
import json
import sys
import time

import chromadb
import requests

OLLAMA = "http://localhost:11434"
MODELO = "bge-m3"
COLECCION = "corpus"


def embed(texto):
    """Devuelve el vector del texto. Prueba las dos rutas de la API de Ollama."""
    r = requests.post(f"{OLLAMA}/api/embeddings",
                      json={"model": MODELO, "prompt": texto}, timeout=120)
    if r.status_code == 404:
        r = requests.post(f"{OLLAMA}/api/embed",
                          json={"model": MODELO, "input": texto}, timeout=120)
        r.raise_for_status()
        return r.json()["embeddings"][0]
    r.raise_for_status()
    return r.json()["embedding"]


def main(entrada, carpeta_indice):
    frags = [json.loads(l) for l in open(entrada, encoding="utf-8") if l.strip()]
    print(f"{len(frags)} fragmentos por indexar. Esto puede tardar varios minutos en CPU.")

    cliente = chromadb.PersistentClient(path=carpeta_indice)
    # Empezamos de cero cada vez: el indice debe poder reconstruirse con un comando.
    try:
        cliente.delete_collection(COLECCION)
    except Exception:
        pass
    col = cliente.create_collection(COLECCION, metadata={"hnsw:space": "cosine"})

    t0 = time.time()
    lote_ids, lote_docs, lote_meta, lote_emb = [], [], [], []
    for i, f in enumerate(frags, 1):
        lote_ids.append(f["id"])
        lote_docs.append(f["texto"])
        lote_meta.append({"documento": f["documento"], "pagina": f["pagina"]})
        lote_emb.append(embed(f["texto"]))
        if len(lote_ids) == 50 or i == len(frags):
            col.add(ids=lote_ids, documents=lote_docs,
                    metadatas=lote_meta, embeddings=lote_emb)
            lote_ids, lote_docs, lote_meta, lote_emb = [], [], [], []
            print(f"  {i}/{len(frags)}  ({time.time() - t0:.0f} s)")

    print(f"\nListo: {col.count()} fragmentos en '{carpeta_indice}' "
          f"({time.time() - t0:.0f} s, modelo {MODELO}).")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
