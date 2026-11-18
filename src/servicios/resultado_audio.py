"""Contrato de audio independiente del codificador y sus dependencias nativas."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResultadoAudio:
    estado: str
    puntajes: dict = field(default_factory=dict)
    codigo: str | None = None

    @classmethod
    def fallido(cls, codigo):
        return cls('FALLIDO', codigo=codigo)
