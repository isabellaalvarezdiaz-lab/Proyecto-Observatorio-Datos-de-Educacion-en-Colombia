"""Recupera los fragmentos mas parecidos a una pregunta.

Uso:  python consultar.py indice "tu pregunta" [k]

No genera texto: solo muestra que fragmentos traeria el sistema y de que
documento y pagina salen. Sirve para evaluar la recuperacion por separado.
"""
import sys

import chromadb

from indexar import COLECCION, embed


def main(carpeta_indice, pregunta, k=5):
    col = chromadb.PersistentClient(path=carpeta_indice).get_collection(COLECCION)
    res = col.query(query_embeddings=[embed(pregunta)], n_results=k)

    print(f"\nPregunta: {pregunta}\n")
    for pos, (doc, meta, dist) in enumerate(
            zip(res["documents"][0], res["metadatas"][0], res["distances"][0]), 1):
        print(f"[{pos}] {meta['documento']}, p. {meta['pagina']}  (distancia {dist:.3f})")
        print("    " + doc[:300].replace("\n", " ") + "...\n")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5)
