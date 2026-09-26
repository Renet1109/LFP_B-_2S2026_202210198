"""Lector estructural auxiliar. Separa los errores sintácticos y semánticos del AFD.

No es un generador de parsers. Su única finalidad es construir los datos de los
reportes, rechazar registros incompletos y continuar en el siguiente elemento.
"""
from .lexer import BLOQUES, ELEMENTOS
from .modelos import Aula, Catedratico, Clase, Curso, Horario


class InterrupcionElemento(Exception):
    pass


class LectorHorario:
    def __init__(self, tokens, errores):
        self.tokens = [t for t in tokens if t.tipo != "COMENTARIO_LINEA"]
        self.i = 0
        self.errores = errores
        self.horario = Horario()

    @property
    def actual(self):
        return self.tokens[min(self.i, len(self.tokens) - 1)]

    def avanzar(self):
        t = self.actual
        if t.tipo != "EOF":
            self.i += 1
        return t

    def problema(self, tipo, descripcion, token=None, fase="SINTACTICO"):
        self.errores.agregar(token or self.actual, tipo, descripcion, fase)

    def exigir(self, lexema=None, tipos=None):
        t = self.actual
        if t.tipo == "ERROR_LEXICO":
            raise InterrupcionElemento()
        if (lexema is not None and t.lexema != lexema) or (tipos is not None and t.tipo not in tipos):
            esperado = repr(lexema) if lexema is not None else " / ".join(tipos)
            self.problema("ESTRUCTURA_INVALIDA", f"Se esperaba {esperado}; se encontró {t.lexema or 'fin de archivo'!r}")
            raise InterrupcionElemento()
        return self.avanzar()

    def sincronizar(self, paradas):
        while self.actual.tipo != "EOF" and self.actual.lexema not in paradas:
            self.avanzar()

    def leer(self):
        try:
            self.exigir("HORARIO")
            self.exigir("{")
        except InterrupcionElemento:
            self.sincronizar(set(BLOQUES[1:]))
        vistos = set()
        while self.actual.tipo != "EOF" and self.actual.lexema != "}":
            seccion = self.actual.lexema
            if seccion not in BLOQUES[1:]:
                if self.actual.tipo != "ERROR_LEXICO":
                    self.problema("SECCION_INVALIDA", "Se esperaba CURSOS, CATEDRATICOS, AULAS o CLASES")
                self.avanzar()
                self.sincronizar(set(BLOQUES[1:]) | {"}"})
                continue
            guardar = seccion not in vistos
            if not guardar:
                self.problema("SECCION_DUPLICADA", f"{seccion} debe aparecer exactamente una vez")
            vistos.add(seccion)
            self.avanzar()
            try:
                self.exigir("{")
            except InterrupcionElemento:
                self.sincronizar(set(BLOQUES[1:]) | {"}"})
                continue
            elemento = {"CURSOS": "curso", "CATEDRATICOS": "catedratico", "AULAS": "aula", "CLASES": "clase"}[seccion]
            while self.actual.tipo != "EOF" and self.actual.lexema != "}" and self.actual.lexema not in BLOQUES:
                antes = self.i
                try:
                    origen = self.exigir(elemento)
                    self.elemento(elemento, origen, guardar)
                    if self.actual.lexema == ",":
                        self.avanzar()
                    elif self.actual.lexema != "}":
                        self.problema("SEPARADOR_FALTANTE", "Falta ',' entre elementos")
                except InterrupcionElemento:
                    if self.i == antes:
                        self.avanzar()
                    self.sincronizar(set(ELEMENTOS) | set(BLOQUES) | {"}"})
            try:
                self.exigir("}")
                self.exigir(";")
            except InterrupcionElemento:
                self.sincronizar(set(BLOQUES[1:]) | {"}"})
        try:
            self.exigir("}")
            self.exigir(";")
        except InterrupcionElemento:
            pass
        if self.actual.tipo != "EOF":
            self.problema("CONTENIDO_SOBRANTE", "Hay contenido después del cierre de HORARIO")
        for nombre in BLOQUES[1:]:
            if nombre not in vistos:
                self.problema("SECCION_FALTANTE", f"Falta la sección obligatoria {nombre}")
        self.validar_referencias()
        return self.horario

    def atributos(self, esquema, opcionales=()):
        self.exigir("[")
        atributos = {}
        while self.actual.lexema != "]":
            clave = self.exigir(tipos=("ATRIBUTO",))
            if clave.lexema not in esquema:
                self.problema("ATRIBUTO_INESPERADO", f"Atributo no admitido en este elemento: {clave.lexema}", clave)
                raise InterrupcionElemento()
            if clave.lexema in atributos:
                self.problema("ATRIBUTO_DUPLICADO", f"Atributo repetido: {clave.lexema}", clave)
                raise InterrupcionElemento()
            self.exigir(":")
            atributos[clave.lexema] = self.exigir(tipos=esquema[clave.lexema]).valor
            if self.actual.lexema == ",":
                self.avanzar()
                if self.actual.lexema == "]":
                    self.problema("ATRIBUTO_FALTANTE", "Falta un atributo después de la coma")
                    raise InterrupcionElemento()
            elif self.actual.lexema != "]":
                self.problema("SEPARADOR_FALTANTE", "Se esperaba ',' o ']' en los atributos")
                raise InterrupcionElemento()
        self.exigir("]")
        faltantes = [c for c in esquema if c not in atributos and c not in opcionales]
        if faltantes:
            self.problema("ATRIBUTO_FALTANTE", "Faltan atributos: " + ", ".join(faltantes))
            raise InterrupcionElemento()
        return atributos

    def elemento(self, clase, origen, guardar):
        self.exigir(":")
        texto = ("CADENA", "CODIGO")
        valor = self.exigir(tipos=("CODIGO",) if clase in ("aula", "clase") else texto).valor
        if clase == "clase":
            self.exigir("con")
            docente = self.exigir(tipos=("CODIGO",)).valor
            self.exigir("en")
            aula = self.exigir(tipos=("CODIGO",)).valor
            a = self.atributos({"dia": ("DIA",), "inicio": ("HORA",), "fin": ("HORA",), "seccion": texto}, ("seccion",))
            if a["fin"] <= a["inicio"]:
                self.problema("INTERVALO_INVALIDO", "El fin debe ser posterior al inicio", origen, "SEMANTICO")
                return
            if guardar:
                self.horario.clases.append(Clase(len(self.horario.clases) + 1, valor, docente, aula,
                                                a["dia"], a["inicio"], a["fin"], a.get("seccion", "").strip() or "SIN SECCION", origen))
            return
        if clase == "curso":
            a = self.atributos({"codigo": ("CODIGO",), "creditos": ("ENTERO",)})
            objeto = Curso(a["codigo"], valor, a["creditos"])
            destino = self.horario.cursos
            positivo = a["creditos"] > 0
        elif clase == "catedratico":
            a = self.atributos({"codigo": ("CODIGO",), "categoria": ("CATEGORIA",)})
            objeto = Catedratico(a["codigo"], valor, a["categoria"])
            destino = self.horario.catedraticos
            positivo = True
        else:
            a = self.atributos({"capacidad": ("ENTERO",), "edificio": texto})
            objeto = Aula(valor, a["capacidad"], a["edificio"])
            destino = self.horario.aulas
            positivo = a["capacidad"] > 0 and bool(a["edificio"].strip())
        if not positivo or not valor.strip():
            self.problema("VALOR_INVALIDO", "Los nombres y edificios no pueden estar vacíos; créditos y capacidad deben ser positivos", origen, "SEMANTICO")
        elif objeto.codigo in destino:
            self.problema("CODIGO_DUPLICADO", f"Código ya definido en la sección: {objeto.codigo}", origen, "SEMANTICO")
        elif guardar:
            destino[objeto.codigo] = objeto

    def validar_referencias(self):
        validas = []
        for clase in self.horario.clases:
            faltantes = []
            for codigo, catalogo, tipo in ((clase.curso, self.horario.cursos, "curso"),
                                           (clase.catedratico, self.horario.catedraticos, "catedrático"),
                                           (clase.aula, self.horario.aulas, "aula")):
                if codigo not in catalogo:
                    faltantes.append(f"{tipo} {codigo}")
            if faltantes:
                self.problema("REFERENCIA_INEXISTENTE", "No está definido: " + ", ".join(faltantes), clase.origen, "SEMANTICO")
            else:
                validas.append(clase)
        self.horario.clases = validas
