"""Extrae el texto de los PDF de una carpeta, guardando el número de página.
Uso:  python extraer.py <carpeta_pdf> <salida.jsonl>
Cada línea de la salida es un fragmento con: documento, página y texto.
Si un PDF no tiene capa de texto (escaneado), lo avisa y no lo incluye.
"""
import json
import sys
from pathlib import Path

import pdfplumber

TAM = 1000      # caracteres por fragmento
SOLAPE = 150    # caracteres que se repiten entre fragmentos consecutivos


def fragmentar(texto, tam=TAM, solape=SOLAPE):
    texto = " ".join(texto.split())
    if not texto:
        return []
    paso = tam - solape
    return [texto[i:i + tam] for i in range(0, len(texto), paso) if texto[i:i + tam].strip()]


def main(carpeta, salida):
    pdfs = sorted(Path(carpeta).glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No hay PDF en {carpeta}")
    n_frag = 0
    with open(salida, "w", encoding="utf-8") as out:
        for pdf in pdfs:
            paginas_con_texto = 0
            with pdfplumber.open(pdf) as doc:
                for i, pagina in enumerate(doc.pages, start=1):
                    texto = pagina.extract_text() or ""
                    if texto.strip():
                        paginas_con_texto += 1
                    for j, frag in enumerate(fragmentar(texto)):
                        out.write(json.dumps({
                            "id": f"{pdf.stem}_p{i}_{j}",
                            "documento": pdf.name,
                            "pagina": i,
                            "texto": frag,
                        }, ensure_ascii=False) + "\n")
                        n_frag += 1
                total = len(doc.pages)
            estado = "OK" if paginas_con_texto else "SIN CAPA DE TEXTO (escaneado, necesita OCR)"
            print(f"{pdf.name}: {paginas_con_texto}/{total} páginas con texto — {estado}")
    print(f"\nTotal de fragmentos: {n_frag} -> {salida}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
