"""Fuentes Graphviz del diseño manual; no generan código del analizador."""
import csv
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent.parent
TRANSICIONES = [
    ('I', 'Espacio, tab, CR, LF; BOM solo inicial', 'I', 'Consumir; actualizar posición'),
    ('I', 'Letra ASCII', 'PAL', 'Consumir inicio de palabra'),
    ('I', 'Dígito ASCII', 'NUM', 'Consumir inicio numérico'),
    ('I', 'Comilla doble', 'TEXTO', 'Consumir apertura; valor vacío'),
    ('I', '#', 'HASH', 'Consumir primer #'),
    ('I', '{ } [ ] : , ;', 'A', 'Consumir y emitir SIMBOLO'),
    ('I', 'EOF', 'A', 'Emitir EOF; no consumir'),
    ('I', 'Cualquier otro carácter', 'E', 'Consumir uno; CARACTER_NO_RECONOCIDO'),
    ('PAL', 'Letra, dígito, guion o _', 'PAL', 'Consumir secuencia completa'),
    ('PAL', 'Otro carácter o EOF', 'A / E', 'No consumir delimitador; reservada, código o error'),
    ('NUM', 'Dígito', 'NUM', 'Consumir'),
    ('NUM', ':', 'HORA', 'Consumir'),
    ('NUM', 'Letra, guion o _', 'MALNUM', 'Consumir; candidato numérico inválido'),
    ('NUM', 'Otro carácter o EOF', 'A', 'No consumir delimitador; emitir ENTERO'),
    ('HORA', 'Letra, dígito, : guion o _', 'HORA', 'Consumir candidato completo'),
    ('HORA', 'Otro carácter o EOF', 'A / E', 'Validar HH:MM y rango; HORA o HORA_FUERA_DE_RANGO'),
    ('MALNUM', 'Letra, dígito, : guion o _', 'MALNUM', 'Consumir candidato completo'),
    ('MALNUM', 'Otro carácter o EOF', 'E', 'No consumir; CODIGO_MAL_FORMADO'),
    ('TEXTO', 'Comilla doble', 'A', 'Consumir cierre; CADENA o CODIGO'),
    ('TEXTO', 'Barra inversa', 'ESCAPE', 'Consumir escape'),
    ('TEXTO', 'CR, LF o EOF', 'E', 'No consumir; CADENA_SIN_CERRAR'),
    ('TEXTO', 'Cualquier otro carácter', 'TEXTO', 'Consumir y añadir al valor'),
    ('ESCAPE', 'EOF', 'E', 'CADENA_SIN_CERRAR'),
    ('ESCAPE', 'CR o LF', 'TEXTO', 'Consumir continuación; no añadir al valor'),
    ('ESCAPE', 'Cualquier otro carácter', 'TEXTO', 'Consumir; n/t/r se decodifican, resto literal'),
    ('HASH', '#', 'COMENTARIO', 'Consumir segundo #'),
    ('HASH', 'Otro carácter o EOF', 'E', 'No consumir; CARACTER_NO_RECONOCIDO'),
    ('COMENTARIO', 'CR, LF o EOF', 'A', 'No consumir; emitir COMENTARIO_LINEA'),
    ('COMENTARIO', 'Cualquier otro carácter', 'COMENTARIO', 'Consumir sin validar contenido'),
]
AFD = r'''digraph AFD {
graph [rankdir=LR, fontname="Arial", bgcolor="white", nodesep=.32, ranksep=.5];
node [fontname="Arial", fontsize=12, shape=circle, style=filled, fillcolor="#e6f3f0"];
edge [fontname="Arial", fontsize=9, color="#55707a"];
inicio [shape=point]; inicio -> I;
A [shape=doublecircle, fillcolor="#b6e4cc", label="A\nEmitir"];
E [shape=doublecircle, fillcolor="#ffd5d5", label="E\nError"];
I -> I [label="blanco / BOM inicial"];
I -> PAL [label="letra"];
I -> NUM [label="dígito"];
I -> TEXTO [label="comilla"];
I -> HASH [label="#"];
I -> A [label="símbolo / EOF"];
I -> E [label="otro"];
PAL -> PAL [label="letra, dígito, -, _"];
PAL -> A [label="otro / EOF; válido *"];
PAL -> E [label="otro / EOF; inválido *"];
NUM -> NUM [label="dígito"];
NUM -> HORA [label=":"];
NUM -> MALNUM [label="letra, -, _"];
NUM -> A [label="otro / EOF *"];
HORA -> HORA [label="letra, dígito, :, -, _"];
HORA -> A [label="otro / EOF; HH:MM válido *"];
HORA -> E [label="otro / EOF; hora inválida *"];
MALNUM -> MALNUM [label="letra, dígito, :, -, _"];
MALNUM -> E [label="otro / EOF *"];
TEXTO -> TEXTO [label="otro"];
TEXTO -> ESCAPE [label="barra inversa"];
TEXTO -> A [label="comilla de cierre"];
TEXTO -> E [label="CR / LF / EOF *"];
ESCAPE -> TEXTO [label="cualquier carácter"];
ESCAPE -> E [label="EOF *"];
HASH -> COMENTARIO [label="#"];
HASH -> E [label="otro / EOF *"];
COMENTARIO -> COMENTARIO [label="otro"];
COMENTARIO -> A [label="CR / LF / EOF *"];
leyenda [shape=note, fillcolor="#f3f6f8", label="* No consume delimitador.\nA/E son salidas, no estados en el bucle.\nLa próxima llamada empieza en I.\nTras la forma se aplica clasificación contextual."];
}'''
CODIGOS = r'''digraph Codigo {
rankdir=LR; bgcolor="white";
node [fontname="Arial", style=filled, fillcolor="#e6f3f0"];
edge [fontname="Arial", fontsize=10];
inicio [shape=point]; inicio -> C0;
CD [shape=doublecircle]; CE [fillcolor="#ffd5d5"];
C0 -> CP [label="letra"];
C0 -> CE [label="otro"];
CP -> CP [label="letra / dígito"];
CP -> CG [label="guion"];
CP -> CE [label="otro"];
CG -> CD [label="dígito"];
CG -> CE [label="otro"];
CD -> CD [label="dígito"];
CD -> CE [label="otro"];
CE -> CE [label="cualquier carácter"];
}'''
CLASES = r'''digraph Clases {
rankdir=TB; bgcolor="white";
node [shape=record, fontname="Arial", fontsize=11, style=filled, fillcolor="#e6f3f0"];
edge [fontname="Arial", fontsize=9];
GUI [label="HorarioScriptApp|abrir / guardar / analizar\lmostrar_resultado()\l"];
Doc [label="Documento|fuente / ruta / resultado\lresaltar()\l"];
Servicio [label="servicio|analizar()\ldetectar_choques()\lcargas() / ocupaciones()\l"];
Lexer [label="AnalizadorLexico|indice / linea / columna\lpendiente / esperado\lsiguiente_token() / analizar()\l"];
Token [label="Token (base del estudiante)|numero / lexema / tipo\llinea / columna\lvalor / inicio / fin\l"];
Errores [label="GestorErrores (base del estudiante)|agregar_error() / agregar()\lhay_errores() / limpiar()\lobtener_errores()\l"];
Error [label="ErrorLexico|tipo / descripcion / fase\llinea / columna / offsets\l"];
Lector [label="LectorHorario|leer() / atributos()\lvalidar_referencias()\l"];
Modelo [label="Horario|cursos / catedraticos\laulas / clases\l"];
Resultado [label="Resultado|tokens / errores / horario\lchoques / tiempo / frecuencias\l"];
Reportes [label="GeneradorReportes|generar() / semanal()\lcarga() / estadisticas()\lerrores() / dot()\l"];
GUI -> Doc [label="1 a varios"];
GUI -> Servicio; GUI -> Reportes;
Doc -> Resultado; Doc -> Lexer [label="resaltado"];
Servicio -> Lexer; Servicio -> Lector; Servicio -> Resultado;
Lexer -> Token; Lexer -> Errores; Errores -> Error;
Lector -> Errores; Lector -> Modelo; Resultado -> Modelo;
Reportes -> Resultado;
}'''


def main():
    destino = BASE / 'docs/diagramas'
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, texto in (('afd', AFD), ('codigos', CODIGOS), ('clases', CLASES)):
        ruta = destino / (nombre + '.dot')
        ruta.write_text(texto, encoding='utf-8')
        if len(sys.argv) > 1:
            for formato in ('svg', 'png'):
                subprocess.run([sys.argv[1], '-T' + formato, str(ruta), '-o', str(ruta.with_suffix('.' + formato))], check=True)
    with (destino / 'transiciones.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(('Estado', 'Entrada', 'Destino', 'Acción'))
        w.writerows(TRANSICIONES)


if __name__ == '__main__':
    main()
