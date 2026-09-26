"""Clase original de William, ampliada con valor interpretado y offsets de origen."""
class Token:
    def __init__(self, numero, lexema, tipo, linea, columna, valor="", inicio=0, fin=0):
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna
        self.valor = valor
        self.inicio = inicio
        self.fin = fin

    def como_dict(self):
        return vars(self).copy()

    def __str__(self):
        return (
            f"{self.numero} | "
            f"{self.lexema} | "
            f"{self.tipo} | "
            f"Linea: {self.linea} | "
            f"Columna: {self.columna}"
        )
