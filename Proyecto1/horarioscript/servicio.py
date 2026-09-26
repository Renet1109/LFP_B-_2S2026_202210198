"""Coordinación del análisis y operaciones de horario sin dependencias de la GUI."""
from collections import Counter
from pathlib import Path
from time import perf_counter

from .lexer import AnalizadorLexico, DIAS
from .lector import LectorHorario
from .modelos import Choque, GestorErrores, Resultado


def leer_archivo(ruta):
    ruta = Path(ruta)
    if ruta.suffix.lower() != ".hor":
        raise ValueError("Seleccione un archivo con extensión .hor")
    # newline='' conserva CRLF en lexemas y offsets; el AFD lo cuenta una sola vez.
    with ruta.open("r", encoding="utf-8-sig", newline="") as archivo:
        return archivo.read()


def detectar_choques(clases):
    choques = []
    por_dia = {d: [] for d in DIAS}
    for clase in clases:
        por_dia[clase.dia].append(clase)
    for dia in DIAS:
        ordenadas = sorted(por_dia[dia], key=lambda c: (c.inicio, c.numero))
        activas = []
        for actual in ordenadas:
            activas = [c for c in activas if c.fin > actual.inicio]
            for anterior in activas:
                motivos = []
                if anterior.catedratico == actual.catedratico:
                    motivos.append("CATEDRATICO")
                if anterior.aula == actual.aula:
                    motivos.append("AULA")
                if motivos:
                    choques.append(Choque(min(anterior.numero, actual.numero), max(anterior.numero, actual.numero),
                                          dia, max(anterior.inicio, actual.inicio), min(anterior.fin, actual.fin), tuple(motivos)))
            activas.append(actual)
    return choques


def analizar(fuente):
    comienzo = perf_counter()
    errores = GestorErrores()
    completos = AnalizadorLexico(fuente, errores).analizar()
    tokens = [t for t in completos if t.tipo not in ("EOF", "ERROR_LEXICO")]
    horario = LectorHorario(completos, errores).leer()
    choques = detectar_choques(horario.clases)
    return Resultado(fuente, tokens, errores.errores, horario, choques,
                     (perf_counter() - comienzo) * 1000, dict(Counter(t.tipo for t in tokens)))


def hora(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def nivel_carga(minutos):
    if minutos <= 240:
        return "BAJA"
    if minutos <= 600:
        return "NORMAL"
    if minutos <= 900:
        return "ALTA"
    return "SATURADA"


def cargas(horario):
    resultado = []
    for docente in horario.catedraticos.values():
        clases = [c for c in horario.clases if c.catedratico == docente.codigo]
        minutos = sum(c.fin - c.inicio for c in clases)
        resultado.append({"docente": docente, "minutos": minutos, "cursos": len({c.curso for c in clases}),
                          "secciones": len({c.seccion for c in clases}), "nivel": nivel_carga(minutos)})
    return resultado


def ocupaciones(horario):
    resultado = []
    for aula in horario.aulas.values():
        clases = [c for c in horario.clases if c.aula == aula.codigo]
        minutos = 0
        # Unión de intervalos: un choque no puede ocupar dos veces el mismo minuto.
        for dia in DIAS:
            intervalos = sorted((c.inicio, c.fin) for c in clases if c.dia == dia)
            fin_anterior = 0
            for inicio, fin in intervalos:
                minutos += max(0, fin - max(inicio, fin_anterior))
                fin_anterior = max(fin_anterior, fin)
        resultado.append({"aula": aula, "clases": len(clases), "minutos": minutos,
                          "porcentaje": minutos / (6 * 15 * 60) * 100})
    return resultado


def sugerir_libres(horario, clase, limite=3):
    """Primeras opciones en saltos de 10 min; conserva duración y excluye la propia clase."""
    duracion = clase.fin - clase.inicio
    candidatos = []
    for dia in DIAS:
        for inicio in range(360, 1260 - duracion + 1, 10):
            fin = inicio + duracion
            if (dia, inicio) == (clase.dia, clase.inicio):
                continue
            if not any(c.numero != clase.numero and c.dia == dia
                       and (c.catedratico == clase.catedratico or c.aula == clase.aula or c.seccion == clase.seccion)
                       and inicio < c.fin and c.inicio < fin for c in horario.clases):
                candidatos.append((dia, inicio, fin))
                if len(candidatos) >= limite:
                    return candidatos
    return candidatos
