"""Motor y sesiones de SQLAlchemy. La sesión se inyecta por request con Depends(get_db)."""
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


def crear_motor(url: str) -> Engine:
    """SQLite necesita check_same_thread=False porque FastAPI atiende requests en varios hilos.
    Una base en memoria usa StaticPool para que todas las sesiones vean la misma conexión."""
    if url.startswith("sqlite"):
        extra = {"poolclass": StaticPool} if ":memory:" in url or url == "sqlite://" else {}
        return create_engine(url, connect_args={"check_same_thread": False}, **extra)
    return create_engine(url, pool_pre_ping=True)


class BaseDeDatos:
    """Agrupa el motor y la fábrica de sesiones de una URL."""

    def __init__(self, url: str) -> None:
        self.motor = crear_motor(url)
        self.SesionLocal = sessionmaker(bind=self.motor, autoflush=False, expire_on_commit=False)

    def crear_tablas(self) -> None:
        from .models import db_models  # noqa: F401  (registra las tablas en Base.metadata)
        Base.metadata.create_all(self.motor)

    def sesion(self) -> Iterator[Session]:
        db = self.SesionLocal()
        try:
            yield db
        finally:
            db.close()
