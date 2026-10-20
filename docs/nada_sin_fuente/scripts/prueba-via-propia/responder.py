"""Responde una pregunta usando SOLO los fragmentos recuperados, con cita.

Uso:  python responder.py indice "tu pregunta" [k]

Aplica el protocolo de consulta: cita obligatoria de documento y pagina, y
abstencion explicita cuando la respuesta no esta en los fragmentos.
"""
import sys

import chromadb
import requests

from indexar import COLECCION, OLLAMA, embed

MODELO_TEXTO = "llama3.2:3b"

PROTOCOLO = """Responde unicamente con la informacion de los fragmentos que aparecen abajo.
Cita siempre el documento y la pagina en el formato [documento, p. X].
Si la respuesta no esta en los fragmentos, responde exactamente:
"No esta en las fuentes."
No completes con conocimiento propio. Responde en espanol y en menos de 120 palabras.

FRAGMENTOS:
{contexto}

PREGUNTA: {pregunta}
"""


def main(carpeta_indice, pregunta, k=5):
    col = chromadb.PersistentClient(path=carpeta_indice).get_collection(COLECCION)
    res = col.query(query_embeddings=[embed(pregunta)], n_results=k)

    contexto = "\n\n".join(
        f"[{m['documento']}, p. {m['pagina']}] {d}"
        for d, m in zip(res["documents"][0], res["metadatas"][0]))

    r = requests.post(f"{OLLAMA}/api/generate", json={
        "model": MODELO_TEXTO,
        "prompt": PROTOCOLO.format(contexto=contexto, pregunta=pregunta),
        "stream": False,
        "options": {"temperature": 0, "num_predict": 200},
    }, timeout=600)
    r.raise_for_status()

    print(f"\nPregunta: {pregunta}\n")
    print("Respuesta:\n" + r.json()["response"].strip())
    print("\nFragmentos entregados al modelo:")
    for m in res["metadatas"][0]:
        print(f"  - {m['documento']}, p. {m['pagina']}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 5)
