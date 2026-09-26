"""AFD escrito a mano: no usa re, split, find ni métodos de clasificación de cadenas.

El AFD reconoce formas. Una validación contextual finita distingue valores de
dia/codigo/hora sin confundir nombres de personas con códigos mal formados.
Los comentarios también son tokens y conservan sus caracteres originales.
"""
from .modelos import GestorErrores, Token

DIAS = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO")
CATEGORIAS = ("TITULAR", "INTERINO", "AUXILIAR")
BLOQUES = ("HORARIO", "CURSOS", "CATEDRATICOS", "AULAS", "CLASES")
ELEMENTOS = ("curso", "catedratico", "aula", "clase")
ATRIBUTOS = ("codigo", "creditos", "categoria", "capacidad", "edificio",
             "dia", "inicio", "fin", "seccion")
SIMBOLOS = "{}[]:,;"


def letra(c):
    return "A" <= c <= "Z" or "a" <= c <= "z"


def digito(c):
    return "0" <= c <= "9"


def codigo_valido(texto):
    """Sub-AFD C0 -> CP -> CG -> CD. BD2-0812 es válido según el ejemplo."""
    estado = "C0"
    for c in texto:
        if estado == "C0" and letra(c):
            estado = "CP"
        elif estado == "CP" and (letra(c) or digito(c)):
            pass
        elif estado == "CP" and c == "-":
            estado = "CG"
        elif estado in ("CG", "CD") and digito(c):
            estado = "CD"
        else:
            return False
    return estado == "CD"


def minutos_validos(texto):
    if len(texto) != 5 or texto[2] != ":":
        return None
    if not (digito(texto[0]) and digito(texto[1]) and digito(texto[3]) and digito(texto[4])):
        return None
    h = (ord(texto[0]) - 48) * 10 + ord(texto[1]) - 48
    m = (ord(texto[3]) - 48) * 10 + ord(texto[4]) - 48
    total = h * 60 + m
    return total if m < 60 and 360 <= total <= 1260 else None


class AnalizadorLexico:
    def __init__(self, fuente, errores=None):
        self.fuente = fuente
        self.errores = errores if errores is not None else GestorErrores()
        self.indice = 0
        self.linea = 1
        self.columna = 1
        self.numero = 0
        self.pendiente = None
        self.esperado = None
        self.estados_visitados = set()

    def _actual(self):
        return self.fuente[self.indice] if self.indice < len(self.fuente) else ""

    def _avanzar(self):
        """Consume un carácter lógico; conserva CRLF y usa tabulaciones de 4 columnas."""
        c = self._actual()
        if not c:
            return ""
        self.indice += 1
        if c == "\r":
            if self._actual() == "\n":
                c += self.fuente[self.indice]
                self.indice += 1
            self.linea += 1
            self.columna = 1
        elif c == "\n":
            self.linea += 1
            self.columna = 1
        elif c == "\t":
            self.columna += 4 - ((self.columna - 1) % 4)
        elif c != "\ufeff" or self.indice != 1:
            self.columna += 1
        return c

    def _emitir(self, lexema, tipo, valor, linea, columna, inicio, error=None):
        # Un comentario no interrumpe la expectativa entre atributo y valor.
        if tipo not in ("SIMBOLO", "COMENTARIO_LINEA", "EOF"):
            esperado = self.esperado
            self.esperado = None
            if error is None:
                if esperado == "codigo" and tipo != "CODIGO":
                    error = ("CODIGO_MAL_FORMADO", "Código mal formado: se espera prefijo alfanumérico iniciado en letra, guion y dígitos")
                elif esperado == "dia" and tipo != "DIA":
                    error = ("DIA_NO_RECONOCIDO", "Día no reconocido; use LUNES a SABADO, sin comillas")
                elif esperado == "hora" and tipo != "HORA":
                    error = ("HORA_FUERA_DE_RANGO", "Hora fuera de rango o formato; use HH:MM entre 06:00 y 21:00")
                elif esperado == "categoria" and tipo != "CATEGORIA":
                    error = ("CATEGORIA_NO_RECONOCIDA", "Categoría no reconocida; use TITULAR, INTERINO o AUXILIAR")
            elif error[0] in ("PALABRA_NO_RECONOCIDA", "CODIGO_MAL_FORMADO"):
                if esperado == "dia":
                    error = ("DIA_NO_RECONOCIDO", "Día no reconocido; use LUNES a SABADO")
                elif esperado == "hora":
                    error = ("HORA_FUERA_DE_RANGO", "Hora fuera de rango o formato; use HH:MM entre 06:00 y 21:00")
                elif esperado == "categoria":
                    error = ("CATEGORIA_NO_RECONOCIDA", "Categoría no reconocida")

        if tipo != "COMENTARIO_LINEA":
            if tipo == "SIMBOLO" and lexema == ":":
                self.esperado = self.pendiente
                self.pendiente = None
            elif tipo != "EOF":
                self.pendiente = None
                if tipo == "SIMBOLO":
                    self.esperado = None
                elif error is None and tipo in ("ATRIBUTO", "RESERVADA_ELEMENTO", "RESERVADA_RELACION"):
                    if valor in ("codigo", "aula", "clase"):
                        self.pendiente = "codigo"
                    elif valor == "dia":
                        self.pendiente = "dia"
                    elif valor in ("inicio", "fin"):
                        self.pendiente = "hora"
                    elif valor == "categoria":
                        self.pendiente = "categoria"
                    elif valor in ("con", "en"):
                        self.esperado = "codigo"

        if error is None and tipo != "EOF":
            self.numero += 1
        token = Token(self.numero if error is None else 0, lexema,
                      "ERROR_LEXICO" if error else tipo, linea, columna,
                      valor, inicio, self.indice)
        if error:
            self.errores.agregar(token, error[0], error[1])
        return token

    def siguiente_token(self):
        estado = "I"
        lexema = ""
        valor = ""
        linea, columna, inicio = self.linea, self.columna, self.indice
        while True:
            self.estados_visitados.add(estado)
            c = self._actual()
            if estado == "I":
                if c and (c in " \t\r\n" or (c == "\ufeff" and self.indice == 0)):
                    self._avanzar()
                    linea, columna, inicio = self.linea, self.columna, self.indice
                    continue
                if not c:
                    return self._emitir("", "EOF", "", linea, columna, inicio)
                if c in SIMBOLOS:
                    self._avanzar()
                    return self._emitir(c, "SIMBOLO", c, linea, columna, inicio)
                lexema += self._avanzar()
                if letra(c):
                    estado = "PAL"
                elif digito(c):
                    estado = "NUM"
                elif c == '"':
                    estado = "TEXTO"
                elif c == "#":
                    estado = "HASH"
                else:
                    return self._emitir(lexema, "", lexema, linea, columna, inicio,
                                        ("CARACTER_NO_RECONOCIDO", f"Carácter no reconocido: {c!r}"))
            elif estado == "PAL":
                if c and (letra(c) or digito(c) or c in "-_"):
                    lexema += self._avanzar()
                    continue
                tipo = None
                for grupo, nombre in ((BLOQUES, "RESERVADA_BLOQUE"), (ELEMENTOS, "RESERVADA_ELEMENTO"),
                                      (("con", "en"), "RESERVADA_RELACION"), (ATRIBUTOS, "ATRIBUTO"),
                                      (DIAS, "DIA"), (CATEGORIAS, "CATEGORIA")):
                    if lexema in grupo:
                        tipo = nombre
                        break
                if tipo is None and codigo_valido(lexema):
                    tipo = "CODIGO"
                error = None
                if tipo is None:
                    es_codigo = self.esperado == "codigo" or "-" in lexema or "_" in lexema
                    error = ("CODIGO_MAL_FORMADO" if es_codigo else "PALABRA_NO_RECONOCIDA",
                             "Código mal formado" if es_codigo else "Palabra no reconocida; revise mayúsculas y ortografía")
                return self._emitir(lexema, tipo or "", lexema, linea, columna, inicio, error)
            elif estado == "NUM":
                if c and digito(c):
                    lexema += self._avanzar()
                elif c == ":":
                    lexema += self._avanzar()
                    estado = "HORA"
                elif c and (letra(c) or c in "-_"):
                    lexema += self._avanzar()
                    estado = "MALNUM"
                else:
                    # Conversión manual: evita el límite de int(str) en literales enormes.
                    numero = 0
                    for d in lexema:
                        numero = numero * 10 + ord(d) - 48
                    return self._emitir(lexema, "ENTERO", numero, linea, columna, inicio)
            elif estado in ("HORA", "MALNUM"):
                if c and (letra(c) or digito(c) or c in ":-_"):
                    lexema += self._avanzar()
                else:
                    minutos = minutos_validos(lexema) if estado == "HORA" else None
                    error = None
                    if minutos is None:
                        error = (("HORA_FUERA_DE_RANGO", "Hora fuera de rango o formato; use HH:MM entre 06:00 y 21:00")
                                 if estado == "HORA" else ("CODIGO_MAL_FORMADO", "El código debe comenzar con una letra"))
                    return self._emitir(lexema, "HORA", minutos, linea, columna, inicio, error)
            elif estado == "TEXTO":
                if not c or c in "\r\n":
                    return self._emitir(lexema, "", valor, linea, columna, inicio,
                                        ("CADENA_SIN_CERRAR", "Cadena sin cerrar"))
                lexema += self._avanzar()
                if c == '"':
                    tipo = "CODIGO" if codigo_valido(valor) else "CADENA"
                    return self._emitir(lexema, tipo, valor, linea, columna, inicio)
                if c == "\\":
                    estado = "ESCAPE"
                else:
                    valor += c
            elif estado == "ESCAPE":
                if not c:
                    return self._emitir(lexema, "", valor, linea, columna, inicio,
                                        ("CADENA_SIN_CERRAR", "Cadena sin cerrar"))
                lexema += self._avanzar()
                # Una nueva línea física escapada es continuación, no contenido.
                if c not in "\r\n":
                    valor += {"n": "\n", "t": "\t", "r": "\r"}.get(c, c)
                estado = "TEXTO"
            elif estado == "HASH":
                if c == "#":
                    lexema += self._avanzar()
                    estado = "COMENTARIO"
                else:
                    return self._emitir(lexema, "", lexema, linea, columna, inicio,
                                        ("CARACTER_NO_RECONOCIDO", "Carácter no reconocido: '#' (un comentario inicia con ##)"))
            elif estado == "COMENTARIO":
                if not c or c in "\r\n":
                    return self._emitir(lexema, "COMENTARIO_LINEA", lexema, linea, columna, inicio)
                lexema += self._avanzar()

    def analizar(self):
        """Incluye errores y EOF para que el lector estructural pueda recuperarse."""
        tokens = []
        while True:
            token = self.siguiente_token()
            tokens.append(token)
            if token.tipo == "EOF":
                return tokens
