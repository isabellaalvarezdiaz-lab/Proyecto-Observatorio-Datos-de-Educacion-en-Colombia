"""Asistente del observatorio: RAG sobre los documentos del proyecto + herramientas sobre la base.

Regla "Nada sin fuente" (la del protocolo v2 del equipo):
  * Las cifras SOLO salen de las herramientas, que leen la base de la API (los mismos CSV que
    producen los scripts). El modelo de lenguaje nunca pone un número propio.
  * El texto de apoyo sale de los documentos (informe final en PDF, README y diccionarios), y
    cada fragmento lleva su documento y su sección o página.
  * Si hay un LLM configurado, solo redacta. Su respuesta se revisa: si trae un número que no está
    en las cifras, en los fragmentos o en la pregunta, se descarta y se responde con la plantilla.

Recuperación: BM25 sobre fragmentos (secciones de Markdown y páginas del PDF), sin servicios
externos ni embeddings, para que funcione igual en el portátil, en Docker y en CI.
"""
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import db_models as m
from ..models import schemas as s
from .eficiencia import normalizar

log = logging.getLogger("observatorio")

DOCUMENTOS_MD = ["README.md", "docs/diccionario_riesgo.md", "docs/diccionario_imputacion.md",
                 "docs/diccionario_resultados_oe2_oe3.md", "docs/diccionario_base_integrada.md",
                 "docs/diccionario_tabla_maestra.md"]
INFORME = "docs/informe_final.pdf"
VACIAS = set("""a al algo como con cual cuales cuando de del el ella en entre es esa ese eso esta este
esto fue ha han hay la las lo los mas me mi muy no o para pero por que qué se ser si sin sobre son su sus
tan te tiene un una uno y ya cuanto cuánto cuál dame dime explica explicame""".split())
GENERICAS = {"universidad", "de", "del", "la", "y", "el", "los", "las", "tecnologica", "nacional",
             "colombia", "colegio", "mayor", "francisco", "jose"}
UNAD = 225709
NACIONAL = 225701


def tokens(texto: str) -> list[str]:
    return [t for t in re.findall(r"[a-zñ0-9]+", normalizar(texto)) if t not in VACIAS and len(t) > 1]


@dataclass
class Trozo:
    documento: str
    ubicacion: str
    texto: str


def trocear_markdown(ruta: Path, nombre: str, max_chars: int = 1500) -> list[Trozo]:
    trozos, titulo, buf = [], "inicio", []

    def cerrar() -> None:
        texto = "\n".join(buf).strip()
        for i in range(0, len(texto), max_chars):
            parte = texto[i:i + max_chars].strip()
            if len(parte) > 40:
                trozos.append(Trozo(nombre, f"sección «{titulo}»", parte))

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{1,4} ", linea):
            cerrar()
            titulo, buf = linea.lstrip("# ").strip(), []
        else:
            buf.append(linea)
    cerrar()
    return trozos


def trocear_pdf(ruta: Path, nombre: str) -> list[Trozo]:
    try:
        from pypdf import PdfReader
    except ImportError:                                       # pragma: no cover
        log.warning("pypdf no está instalado: el asistente no lee %s", nombre)
        return []
    trozos = []
    for i, pagina in enumerate(PdfReader(str(ruta)).pages, start=1):
        texto = " ".join((pagina.extract_text() or "").split())
        for j in range(0, len(texto), 1500):
            if len(texto[j:j + 1500]) > 40:
                trozos.append(Trozo(nombre, f"página {i} del PDF", texto[j:j + 1500]))
    return trozos


class IndiceBM25:
    def __init__(self, trozos: list[Trozo], k1: float = 1.5, b: float = 0.75) -> None:
        self.trozos = trozos
        self.k1, self.b = k1, b
        self.tf = [Counter(tokens(t.texto + " " + t.ubicacion)) for t in trozos]
        self.largo = [sum(c.values()) for c in self.tf]
        self.prom = sum(self.largo) / max(len(self.largo), 1)
        df = Counter(t for c in self.tf for t in c)
        n = len(trozos)
        self.idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    @classmethod
    def desde_repo(cls, raiz: Path) -> "IndiceBM25":
        trozos: list[Trozo] = []
        for rel in DOCUMENTOS_MD:
            if (raiz / rel).exists():
                trozos += trocear_markdown(raiz / rel, rel)
        if (raiz / INFORME).exists():
            trozos += trocear_pdf(raiz / INFORME, "informe final (docs/informe_final.pdf)")
        log.info("Índice del asistente: %d fragmentos", len(trozos))
        return cls(trozos)

    def buscar(self, consulta: str, k: int = 3, cobertura_min: float = 0.5) -> list[s.Fragmento]:
        """Los k fragmentos con mayor BM25 que contienen al menos la mitad de las palabras de la
        consulta (y al menos dos): así una pregunta ajena al proyecto no trae un fragmento cualquiera."""
        q = list(dict.fromkeys(tokens(consulta)))
        if not q:
            return []
        puntos = []
        for i, tf in enumerate(self.tf):
            presentes = [t for t in q if t in tf]
            if len(presentes) < max(min(2, len(q)), cobertura_min * len(q)):
                puntos.append(0.0)
                continue
            p = 0.0
            for t in presentes:
                f = tf[t]
                p += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.largo[i] / self.prom))
            puntos.append(p)
        mejores = sorted(range(len(puntos)), key=lambda i: -puntos[i])[:k]
        return [s.Fragmento(documento=self.trozos[i].documento, ubicacion=self.trozos[i].ubicacion,
                            texto=self.trozos[i].texto[:700], puntaje=round(puntos[i], 3))
                for i in mejores if puntos[i] > 0]


# ---------------------------------------------------------------- herramientas
class Herramientas:
    """Cada herramienta lee la base y devuelve cifras con su fuente."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.unis = list(self.db.scalars(select(m.Universidad)))
        n = len(self.unis) or 1
        self.conteo = Counter(t for u in self.unis for t in set(tokens(u.nombre)) - GENERICAS)
        self.idf = {t: math.log(1 + n / c) for t, c in self.conteo.items()}

    def universidad(self, pregunta: str) -> m.Universidad | None:
        """La universidad que nombra la pregunta. Basta una palabra propia de un solo nombre
        («chocó», «antioquia», «valle»); si hay varias candidatas gana la de más palabras propias."""
        q = set(tokens(pregunta))
        texto = " ".join(tokens(pregunta))
        if "unad" in q or "abierta" in q:
            return self.db.get(m.Universidad, UNAD)
        if re.search(r"universidad nacional(?! abierta)", texto) and not q & {"pedagogica", "abierta"}:
            return self.db.get(m.Universidad, NACIONAL)
        mejor, mejor_p = None, (0.0, 0)
        for u in self.unis:
            todos = set(tokens(u.nombre))
            propios = todos - GENERICAS
            comunes = propios & q
            if not comunes:
                continue
            unica = any(self.conteo[t] == 1 for t in comunes)
            p = sum(self.idf[t] for t in comunes) / sum(self.idf[t] for t in propios)
            puntaje = (p, len(todos & q))       # en empate gana la que comparte más palabras
            if (unica or p >= 0.5) and puntaje > mejor_p:
                mejor, mejor_p = u, puntaje
        return mejor

    def eficiencia(self, u: m.Universidad) -> list[s.Cifra]:
        filas = self.db.scalars(select(m.Eficiencia).where(m.Eficiencia.pte_codigo == u.pte_codigo,
                                                           m.Eficiencia.modelo == "principal")
                                .order_by(m.Eficiencia.anio))
        return [c for e in filas for c in (
            s.Cifra(descripcion=f"Eficiencia corregida {e.anio} (modelo principal)", valor=e.eficiencia_corregida,
                    fuente="GET /eficiencia · oe3_eficiencia.csv"),
            s.Cifra(descripcion=f"IC 95 % inferior {e.anio}", valor=e.ic95_inf, fuente="GET /eficiencia · oe3_eficiencia.csv"),
            s.Cifra(descripcion=f"IC 95 % superior {e.anio}", valor=e.ic95_sup, fuente="GET /eficiencia · oe3_eficiencia.csv"))]

    def cola(self, u: m.Universidad | None) -> list[s.Cifra]:
        q = select(m.RiesgoCola).where(m.RiesgoCola.anio == 2024)
        q = q.where(m.RiesgoCola.pte_codigo == u.pte_codigo) if u else q.where(m.RiesgoCola.nombre == "nacional")
        r = self.db.scalars(q).first()
        if r is None:
            return []
        f = "GET /riesgo/cola · riesgo_puntaje.csv"
        cifras = [s.Cifra(descripcion=f"VaR 5 % del puntaje 2024 ({r.nombre})", valor=r.var, fuente=f),
                  s.Cifra(descripcion=f"Puntaje medio 2024 ({r.nombre})", valor=r.media, fuente=f)]
        if r.cvar is not None:                                 # suprimido si la cola es muy pequeña
            cifras.insert(1, s.Cifra(descripcion=f"CVaR 5 % del puntaje 2024 ({r.nombre})", valor=r.cvar, fuente=f))
            cifras.append(s.Cifra(descripcion="Brecha de cola 2024 (media − CVaR)", valor=r.brecha_cola, fuente=f))
        return cifras

    def kupiec(self, u: m.Universidad | None) -> list[s.Cifra]:
        q = select(m.Kupiec)
        q = q.where(m.Kupiec.pte_codigo == u.pte_codigo) if u else q.where(m.Kupiec.nombre == "nacional")
        r = self.db.scalars(q).first()
        if r is None:
            return []
        f = "GET /riesgo/backtesting/kupiec · riesgo_kupiec.csv"
        return [s.Cifra(descripcion=f"Tasa 2024 por debajo del VaR 2023 ({r.nombre})", valor=r.tasa_2024, fuente=f),
                s.Cifra(descripcion="Tasa nacional de referencia 2024", valor=r.tasa_ref_nacional, fuente=f),
                s.Cifra(descripcion="p-valor de la prueba relativa", valor=r.p_relativo, fuente=f)]

    def stress(self, u: m.Universidad | None) -> list[s.Cifra]:
        f = "GET /stress/escenarios · riesgo_stress_*.csv"
        esc = "E6 + gratuidad por matrícula de pregrado"
        if u:
            r = self.db.scalars(select(m.StressUniversidad).where(
                m.StressUniversidad.pte_codigo == u.pte_codigo, m.StressUniversidad.modelo == "principal",
                m.StressUniversidad.escenario == esc)).first()
            if r is None:
                return []
            return [s.Cifra(descripcion="Eficiencia base 2024 (principal)", valor=r.eficiencia_base, fuente=f),
                    s.Cifra(descripcion="Eficiencia sumando la gratuidad (E6)", valor=r.eficiencia_escenario, fuente=f),
                    s.Cifra(descripcion="Puesto base", valor=r.puesto_base, fuente=f),
                    s.Cifra(descripcion="Puesto con la gratuidad (E6)", valor=r.puesto_escenario, fuente=f)]
        r = self.db.scalars(select(m.StressResumen).where(m.StressResumen.modelo == "principal",
                                                          m.StressResumen.escenario == esc)).first()
        return [] if r is None else [
            s.Cifra(descripcion="Universidades en la frontera con la gratuidad (E6)", valor=r.n_frontera, fuente=f),
            s.Cifra(descripcion="Spearman con el orden base (E6)", valor=r.spearman_con_base, fuente=f)]

    def malmquist(self, u: m.Universidad) -> list[s.Cifra]:
        r = self.db.scalars(select(m.Malmquist).where(m.Malmquist.pte_codigo == u.pte_codigo,
                                                      m.Malmquist.modelo == "principal",
                                                      m.Malmquist.version == "nominal")).first()
        f = "GET /malmquist · oe2_malmquist.csv"
        return [] if r is None else [s.Cifra(descripcion="Índice de Malmquist 2023→2024", valor=r.malmquist, fuente=f),
                                     s.Cifra(descripcion="Cambio de eficiencia", valor=r.cambio_eficiencia, fuente=f),
                                     s.Cifra(descripcion="Cambio tecnológico", valor=r.cambio_tecnologico, fuente=f)]

    def escrita(self, u: m.Universidad | None) -> list[s.Cifra]:
        q = select(m.ImputacionUniversidad).where(m.ImputacionUniversidad.anio == 2024)
        q = q.where(m.ImputacionUniversidad.pte_codigo == u.pte_codigo) if u else \
            q.where(m.ImputacionUniversidad.nombre == "nacional")
        r = self.db.scalars(q).first()
        f = "GET /imputacion/escrita · imputacion_escrita_universidades.csv"
        return [] if r is None else [
            s.Cifra(descripcion=f"Ceros en Escrita 2024 ({r.nombre})", valor=r.n_ceros_escrita, fuente=f),
            s.Cifra(descripcion="Global 2024 con el promedio de 4 módulos (global_c)", valor=r.global_c, fuente=f),
            s.Cifra(descripcion="Global 2024 con Escrita imputada por PMM (global_d)", valor=r.global_d, fuente=f)]


INTENCIONES = [
    ("kupiec", ("kupiec", "backtest", "backtesting")),
    ("stress", ("stress", "estres", "recorte", "gratuidad", "presupuesto", "escenario")),
    ("cola", ("cvar", "var", "cola", "riesgo", "rezagado", "rezagados")),
    ("malmquist", ("malmquist", "productividad")),
    ("escrita", ("escrita", "imputacion", "imputar", "ceros", "cero")),
    ("eficiencia", ("eficiencia", "eficiente", "frontera", "dea")),
]


def intenciones(pregunta: str) -> list[str]:
    q = set(tokens(pregunta))
    return [n for n, claves in INTENCIONES if q & set(claves)]


# ---------------------------------------------------------------- redacción
def formato(v: float) -> str:
    if float(v).is_integer():
        return f"{int(v)}"
    return f"{v:.4f}".rstrip("0").rstrip(".").replace(".", ",")


def formato_cifra(c: s.Cifra) -> str:
    if "p-valor" in c.descripcion and c.valor < 1e-6:
        return "menor que 0,000001"
    return formato(c.valor)


def plantilla(cifras: list[s.Cifra], fuentes: list[s.Fragmento]) -> str:
    """Respuesta sin LLM: las cifras con su descripción y, si no hay cifras, el fragmento citado."""
    if not cifras and not fuentes:
        return ("No encontré cifras ni documentos del proyecto que respondan esa pregunta. "
                "Prefiero no responder sin fuente.")
    if not cifras:
        f = fuentes[0]
        extracto = f.texto if len(f.texto) <= 400 else f.texto[:400].rsplit(" ", 1)[0] + " […]"
        return f"Según {f.documento} ({f.ubicacion}): «{extracto}»"
    partes = [f"{c.descripcion}: {formato_cifra(c)}." for c in cifras]
    if fuentes:
        partes.append(f"Contexto en {fuentes[0].documento}, {fuentes[0].ubicacion}.")
    return " ".join(partes)


def numeros(texto: str) -> list[float]:
    vals = []
    for t in re.findall(r"\d+(?:[.,]\d+)*", texto):
        t2 = t.replace(".", "").replace(",", ".") if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", t) else t.replace(",", ".")
        try:
            vals.append(float(t2))
        except ValueError:
            continue
    return vals


def numeros_permitidos(pregunta: str, cifras: list[s.Cifra], fuentes: list[s.Fragmento]) -> set[float]:
    ok: set[float] = set(numeros(pregunta))
    for f in fuentes:
        ok |= set(numeros(f.texto))
    for c in cifras:
        for d in range(0, 5):
            ok |= {round(c.valor, d), round(c.valor * 100, d)}
    ok |= {2023.0, 2024.0, 5.0, 95.0}
    return ok


def revisar_numeros(texto: str, permitidos: set[float]) -> list[float]:
    """Números del texto que no salen de ninguna fuente."""
    return [v for v in numeros(texto) if not any(abs(v - p) <= 0.006 for p in permitidos)]


class LLM(Protocol):
    async def redactar(self, sistema: str, usuario: str) -> str: ...


class LLMAnthropic:
    """Cliente mínimo de la API de mensajes de Anthropic (asíncrono)."""

    def __init__(self, api_key: str, modelo: str, url: str, timeout: float) -> None:
        self.api_key, self.modelo, self.url, self.timeout = api_key, modelo, url, timeout

    async def redactar(self, sistema: str, usuario: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as cliente:
            r = await cliente.post(self.url, headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01",
                                                      "content-type": "application/json"},
                                   json={"model": self.modelo, "max_tokens": 600, "system": sistema,
                                         "messages": [{"role": "user", "content": usuario}]})
            r.raise_for_status()
            return "".join(b.get("text", "") for b in r.json()["content"])


SISTEMA = ("Eres el asistente del Observatorio de Datos de Educación (USTA). Responde en español, en 2 a 5 "
           "oraciones, usando SOLO las cifras y los fragmentos dados. No agregues ningún número que no esté "
           "ahí. Si la información no alcanza, dilo. Menciona de qué documento sale cada idea.")


class Asistente:
    def __init__(self, db: Session, indice: IndiceBM25, llm: LLM | None) -> None:
        self.h = Herramientas(db)
        self.indice = indice
        self.llm = llm

    def reunir(self, pregunta: str) -> tuple[list[s.Cifra], list[s.Fragmento]]:
        u = self.h.universidad(pregunta)
        cifras: list[s.Cifra] = []
        for intencion in intenciones(pregunta):
            if intencion in ("eficiencia", "malmquist") and u is None:
                continue
            cifras += getattr(self.h, intencion)(u)
        consulta = pregunta + (f" {u.nombre}" if u else "")
        return cifras, self.indice.buscar(consulta, k=3)

    async def responder(self, p: s.Pregunta) -> s.Respuesta:
        cifras, fuentes = self.reunir(p.pregunta)
        base = plantilla(cifras, fuentes)
        if not (p.usar_llm and self.llm and (cifras or fuentes)):
            return s.Respuesta(respuesta=base, modo="plantilla", cifras=cifras, fuentes=fuentes)
        contexto = "CIFRAS:\n" + "\n".join(f"- {c.descripcion}: {formato_cifra(c)} ({c.fuente})" for c in cifras) + \
            "\n\nFRAGMENTOS:\n" + "\n".join(f"[{f.documento}, {f.ubicacion}] {f.texto}" for f in fuentes)
        try:
            texto = await self.llm.redactar(SISTEMA, f"{contexto}\n\nPREGUNTA: {p.pregunta}")
        except Exception as exc:                               # el LLM es opcional: nunca tumba la API
            log.warning("El LLM falló (%s); se responde con la plantilla", exc)
            return s.Respuesta(respuesta=base, modo="plantilla", cifras=cifras, fuentes=fuentes)
        extra = revisar_numeros(texto, numeros_permitidos(p.pregunta, cifras, fuentes))
        if extra:
            log.warning("Respuesta del LLM descartada: números sin fuente %s", extra)
            return s.Respuesta(respuesta=base, modo="llm_rechazado", cifras=cifras, fuentes=fuentes)
        return s.Respuesta(respuesta=texto.strip(), modo="llm", cifras=cifras, fuentes=fuentes)
