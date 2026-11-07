"""Decorador propio: registra en el log el tiempo de cada cálculo de los servicios."""
import functools
import logging
import time
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")
log = logging.getLogger("observatorio")


def medir_tiempo(func: Callable[P, R]) -> Callable[P, R]:
    """Mide cuánto tarda la función y lo escribe en el log con su nombre calificado."""
    @functools.wraps(func)
    def envoltura(*args: P.args, **kwargs: P.kwargs) -> R:
        inicio = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            ms = (time.perf_counter() - inicio) * 1000
            log.info("%s tardó %.1f ms", func.__qualname__, ms)
    return envoltura
