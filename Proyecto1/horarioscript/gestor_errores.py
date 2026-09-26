"""Clases originales de William; conservan sus métodos y añaden fase y offsets."""
class ErrorLexico:
    def __init__(
        self,
        numero,
        lexema,
        tipo,
        descripcion,
        linea,
        columna,
        fase="LEXICO",
        inicio=0,
        fin=0
    ):
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.descripcion = descripcion
        self.linea = linea
        self.columna = columna
        self.fase = fase
        self.inicio = inicio
        self.fin = fin

    def __str__(self):
        return (
            f"{self.numero} | "
            f"{self.lexema} | "
            f"{self.tipo} | "
            f"{self.descripcion} | "
            f"Linea: {self.linea} | "
            f"Columna: {self.columna}"
        )


class GestorErrores:
    def __init__(self):
        self.errores = []

    def agregar_error(
        self,
        lexema,
        tipo,
        descripcion,
        linea,
        columna
    ):
        numero = len(self.errores) + 1

        error = ErrorLexico(
            numero,
            lexema,
            tipo,
            descripcion,
            linea,
            columna
        )

        self.errores.append(error)

    def hay_errores(self):
        return len(self.errores) > 0

    def limpiar(self):
        self.errores.clear()

    def obtener_errores(self):
        return self.errores

    def agregar(self, token, tipo, descripcion, fase="LEXICO"):
        error = ErrorLexico(len(self.errores) + 1, token.lexema, tipo,
                            descripcion, token.linea, token.columna,
                            fase, token.inicio, token.fin)
        self.errores.append(error)
        return error


Diagnostico = ErrorLexico
