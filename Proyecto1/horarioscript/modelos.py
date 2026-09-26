"""Objetos compartidos; las posiciones son de base uno y los offsets de base cero."""
from dataclasses import dataclass, field
from .token import Token
from .gestor_errores import Diagnostico, GestorErrores


@dataclass(frozen=True)
class Curso:
    codigo: str
    nombre: str
    creditos: int


@dataclass(frozen=True)
class Catedratico:
    codigo: str
    nombre: str
    categoria: str


@dataclass(frozen=True)
class Aula:
    codigo: str
    capacidad: int
    edificio: str


@dataclass(frozen=True)
class Clase:
    numero: int
    curso: str
    catedratico: str
    aula: str
    dia: str
    inicio: int
    fin: int
    seccion: str
    origen: Token


@dataclass(frozen=True)
class Choque:
    primera: int
    segunda: int
    dia: str
    inicio: int
    fin: int
    motivos: tuple[str, ...]


@dataclass
class Horario:
    cursos: dict[str, Curso] = field(default_factory=dict)
    catedraticos: dict[str, Catedratico] = field(default_factory=dict)
    aulas: dict[str, Aula] = field(default_factory=dict)
    clases: list[Clase] = field(default_factory=list)


@dataclass
class Resultado:
    fuente: str
    tokens: list[Token]
    errores: list[Diagnostico]
    horario: Horario
    choques: list[Choque]
    milisegundos: float
    frecuencias: dict[str, int]

    @property
    def errores_lexicos(self):
        return [e for e in self.errores if e.fase == "LEXICO"]

    @property
    def correcto(self):
        return not self.errores and not self.choques
