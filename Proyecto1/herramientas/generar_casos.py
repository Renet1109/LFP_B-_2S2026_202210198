"""Crea entradas reproducibles; las expectativas se declaran antes de ejecutarlas."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
VALIDO = '''## Horario Lenguajes Formales - Segundo Semestre 2026
HORARIO {
CURSOS {
curso: "Lenguajes Formales y de Programacion" [codigo: "LFP-0796", creditos: 4],
curso: "Bases de Datos 2" [codigo: "BD2-0812", creditos: 5],
};
CATEDRATICOS {
catedratico: "Otto Rodriguez" [codigo: "DOC-001", categoria: TITULAR],
catedratico: "Vivian Campos" [codigo: "DOC-002", categoria: INTERINO],
};
AULAS {
aula: "A-101" [capacidad: 40, edificio: "T-3"],
aula: "LAB-3" [capacidad: 25, edificio: "T-5"],
};
CLASES {
clase: "LFP-0796" con "DOC-001" en "A-101" [dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "N"],
clase: "BD2-0812" con "DOC-002" en "LAB-3" [dia: MARTES, inicio: 10:20, fin: 12:00, seccion: "A"],
};
};
'''


def agregar_clase(texto, linea):
    return texto.replace("CLASES {\n", "CLASES {\n" + linea + "\n")


def main():
    entrada = BASE / "entrada"
    entrada.mkdir(parents=True, exist_ok=True)
    docente = 'clase: "BD2-0812" con "DOC-001" en "LAB-3" [dia: LUNES, inicio: 07:30, fin: 09:00, seccion: "B+"],'
    aula = 'clase: "BD2-0812" con "DOC-002" en "A-101" [dia: LUNES, inicio: 08:00, fin: 09:00, seccion: "B+"],'
    vacio = 'HORARIO { CURSOS {}; CATEDRATICOS {}; AULAS {}; CLASES {}; };'
    casos = [
        ("01_valido", "Ejemplo del enunciado", VALIDO, [], 0, 2),
        ("02_caracteres", "Recuperación ante @, % y ~", VALIDO.replace("CURSOS {", "@ % ~\nCURSOS {"), ["CARACTER_NO_RECONOCIDO"] * 3, 0, 2),
        ("03_hora_rango", "Hora anterior a 06:00", VALIDO.replace("07:00", "05:59"), ["HORA_FUERA_DE_RANGO"], 0, 1),
        ("04_dia", "DOMINGO no pertenece al lenguaje", VALIDO.replace("dia: LUNES", "dia: DOMINGO"), ["DIA_NO_RECONOCIDO"], 0, 1),
        ("05_codigo", "Código sin guion", VALIDO.replace('codigo: "LFP-0796"', 'codigo: "LFP0796"'), ["CODIGO_MAL_FORMADO"], 0, 1),
        ("06_comentario_eof", "Comentario sin salto final: EOF lo cierra", VALIDO + '## comentario sin cerrar aparente: @ % ~ "', [], 0, 2),
        ("07_cadena", "Cadena sin comilla de cierre", VALIDO.replace('"Lenguajes Formales y de Programacion" [codigo: "LFP-0796", creditos: 4],', '"Cadena sin cerrar'), ["CADENA_SIN_CERRAR"], 0, 1),
        ("08_choque_docente", "Docente simultáneo en dos aulas y secciones", agregar_clase(VALIDO, docente), [], 1, 3),
        ("09_choque_aula", "Aula simultánea con dos docentes", agregar_clase(VALIDO, aula), [], 1, 3),
        ("10_limites", "06:00, 21:00 e intervalos adyacentes", VALIDO.replace("07:00", "06:00").replace("08:40", "07:00").replace("MARTES", "LUNES").replace("10:20", "07:00").replace("12:00", "21:00").replace('en "LAB-3"', 'en "A-101"'), [], 0, 2),
        ("11_vacio", "Catálogos vacíos, sin división por cero", vacio, [], 0, 0),
        ("12_formato_hora", "Hora de un dígito: 7:00", VALIDO.replace("07:00", "7:00"), ["HORA_FUERA_DE_RANGO"], 0, 1),
    ]
    metadatos = []
    for nombre, titulo, fuente, tipos, choques, clases in casos:
        (entrada / f"{nombre}.hor").write_text(fuente, encoding="utf-8")
        metadatos.append({"archivo": nombre + ".hor", "titulo": titulo,
                          "esperado": {"tipos_lexicos": tipos, "choques": choques, "clases_validas": clases}})
    (entrada / "casos.json").write_text(json.dumps(metadatos, ensure_ascii=False, indent=2), encoding="utf-8")
    # Demostración con bloques repartidos durante la semana y un choque visible.
    demo = agregar_clase(VALIDO.replace('seccion: "N"', 'seccion: "B+"').replace('seccion: "A"', 'seccion: "B+"'), docente)
    for linea in (
        'clase: "LFP-0796" con "DOC-001" en "A-101" [dia: MIERCOLES, inicio: 07:00, fin: 08:40, seccion: "B+"],',
        'clase: "BD2-0812" con "DOC-002" en "LAB-3" [dia: JUEVES, inicio: 10:20, fin: 12:00, seccion: "B+"],',
        'clase: "LFP-0796" con "DOC-001" en "A-101" [dia: VIERNES, inicio: 07:00, fin: 08:40, seccion: "B+"],',
        'clase: "BD2-0812" con "DOC-002" en "LAB-3" [dia: SABADO, inicio: 10:20, fin: 12:00, seccion: "B+"],',
    ):
        demo = agregar_clase(demo, linea)
    (entrada / "demo.hor").write_text(demo, encoding="utf-8")
    print(f"{len(casos)} casos y demo.hor generados en {entrada}")


if __name__ == "__main__":
    main()
