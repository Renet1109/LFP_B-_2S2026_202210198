class Token:
    def __init__(self, numero, lexema, tipo, linea, columna):
        self.numero = numero
        self.lexema = lexema
        self.tipo = tipo
        self.linea = linea
        self.columna = columna

    def __str__(self):
        return (
            f"{self.numero} | "
            f"{self.lexema} | "
            f"{self.tipo} | "
            f"Linea: {self.linea} | "
            f"Columna: {self.columna}"
        )