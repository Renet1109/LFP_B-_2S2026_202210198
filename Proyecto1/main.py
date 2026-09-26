"""Inicio de HorarioScript: GUI por defecto, CLI reproducible mediante --analizar."""
import argparse
from pathlib import Path
import sys
import subprocess

from horarioscript import __version__
from horarioscript.reportes import GeneradorReportes, renderizar_dot
from horarioscript.servicio import analizar, leer_archivo


def main():
    parser = argparse.ArgumentParser(description="HorarioScript · William René Toledo Corado · 202210198 · B+")
    parser.add_argument("archivo", nargs="?", help="Archivo .hor que se abre en la interfaz")
    parser.add_argument("--analizar", metavar="ARCHIVO", help="Analiza sin interfaz y genera reportes")
    parser.add_argument("--salida", default="salidas/cli", help="Carpeta para los reportes de consola")
    parser.add_argument("--dot", metavar="EJECUTABLE", help="Ruta opcional a Graphviz para renderizar el DOT")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args()
    if args.analizar:
        try:
            resultado = analizar(leer_archivo(args.analizar))
            rutas = GeneradorReportes(resultado, args.salida, Path(args.analizar).name).generar()
            if args.dot:
                renderizar_dot(rutas["dot"], args.dot)
            print(f"Tokens: {len(resultado.tokens)} | Errores léxicos: {len(resultado.errores_lexicos)} | "
                  f"Otros diagnósticos: {len(resultado.errores)-len(resultado.errores_lexicos)} | Choques: {len(resultado.choques)}")
            print(f"Análisis: {resultado.milisegundos:.2f} ms | Reportes: {Path(args.salida).resolve()}")
            for error in resultado.errores:
                print(f"{error.fase}: {error.tipo} ({error.linea}:{error.columna}) {error.descripcion}")
            return 0 if resultado.correcto else 1
        except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 2
    from horarioscript.gui import HorarioScriptApp
    HorarioScriptApp(args.archivo).mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
