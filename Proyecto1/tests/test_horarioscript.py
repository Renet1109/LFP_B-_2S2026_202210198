"""Pruebas independientes de AFD, lector, intervalos, exportaciones y reportes."""
import ast
import csv
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from horarioscript.lexer import AnalizadorLexico, codigo_valido, minutos_validos
from horarioscript.modelos import Aula, Catedratico, Clase, Curso, Horario, Token
from horarioscript.reportes import GeneradorReportes, exportar_tokens
from horarioscript.servicio import analizar, cargas, detectar_choques, leer_archivo, nivel_carga, ocupaciones, sugerir_libres

BASE = Path(__file__).resolve().parent.parent
VALIDO = (BASE / "entrada/01_valido.hor").read_text(encoding="utf-8")


def lex(fuente):
    lexer = AnalizadorLexico(fuente)
    return lexer, lexer.analizar()


class PruebasLexicas(unittest.TestCase):
    def test_tokens_y_posiciones_exactas(self):
        _, ts = lex('HORARIO {\r\n\tcurso: "Álgebra" [creditos: 4], ## @%\r\n};')
        esperado = [('HORARIO', 'RESERVADA_BLOQUE', 1, 1), ('{', 'SIMBOLO', 1, 9),
                    ('curso', 'RESERVADA_ELEMENTO', 2, 5), (':', 'SIMBOLO', 2, 10),
                    ('"Álgebra"', 'CADENA', 2, 12), ('[', 'SIMBOLO', 2, 22),
                    ('creditos', 'ATRIBUTO', 2, 23), (':', 'SIMBOLO', 2, 31),
                    ('4', 'ENTERO', 2, 33), (']', 'SIMBOLO', 2, 34), (',', 'SIMBOLO', 2, 35),
                    ('## @%', 'COMENTARIO_LINEA', 2, 37), ('}', 'SIMBOLO', 3, 1), (';', 'SIMBOLO', 3, 2)]
        self.assertEqual([(t.lexema, t.tipo, t.linea, t.columna) for t in ts[:-1]], esperado)
        self.assertEqual([t.numero for t in ts[:-1]], list(range(1, 15)))

    def test_nombres_de_atributos_dentro_de_cadenas_no_cambian_contexto(self):
        l, ts = lex('curso: "dia" [codigo: "LFP-0796", creditos: 4]')
        self.assertFalse(l.errores.errores)
        self.assertEqual(ts[2].tipo, "CADENA")

    def test_alfabeto_codigo(self):
        for texto in ('A-1', 'LFP-0796', 'BD2-0812', 'LAB-3', 'A0-000'):
            with self.subTest(texto=texto):
                self.assertTrue(codigo_valido(texto))
        for texto in ('', '0A-1', 'A-', '-1', 'A--1', 'A_1', 'A-1x', 'Á-1', 'A B-1'):
            with self.subTest(texto=texto):
                self.assertFalse(codigo_valido(texto))

    def test_codigos_con_y_sin_comillas(self):
        l, ts = lex('"LFP-0796" DOC-001 "BD2-0812"')
        self.assertFalse(l.errores.errores)
        self.assertEqual([t.tipo for t in ts[:-1]], ["CODIGO"] * 3)

    def test_todos_los_minutos_institucionales(self):
        for h in range(24):
            for m in range(60):
                texto = f"{h:02}:{m:02}"
                self.assertEqual(minutos_validos(texto), h * 60 + m if 360 <= h * 60 + m <= 1260 else None)

    def test_horas_mal_formadas(self):
        for texto in ('6:00', '06:0', '006:00', '06:60', '21:01', '05:59', '07:00x', '07:00:1', '99:99'):
            with self.subTest(texto=texto):
                l, _ = lex(texto)
                self.assertEqual(l.errores.errores[0].tipo, "HORA_FUERA_DE_RANGO")

    def test_contextos_invalidos(self):
        for texto, tipo in (('dia: DOMINGO', 'DIA_NO_RECONOCIDO'), ('dia: "LUNES"', 'DIA_NO_RECONOCIDO'),
                            ('codigo: "SIN GUION"', 'CODIGO_MAL_FORMADO'), ('codigo: 123', 'CODIGO_MAL_FORMADO'),
                            ('inicio: 600', 'HORA_FUERA_DE_RANGO'), ('fin: tarde', 'HORA_FUERA_DE_RANGO'),
                            ('categoria: VISITANTE', 'CATEGORIA_NO_RECONOCIDA')):
            with self.subTest(texto=texto):
                l, _ = lex(texto)
                self.assertEqual([e.tipo for e in l.errores.errores], [tipo])

    def test_comentario_preserva_contexto(self):
        l, ts = lex('dia ## comentario\n: ## otro\nLUNES')
        self.assertFalse(l.errores.errores)
        self.assertEqual(ts[-2].tipo, 'DIA')

    def test_comentario_eof_y_caracteres_internos(self):
        l, ts = lex('## @ ~ " %')
        self.assertFalse(l.errores.errores)
        self.assertEqual(ts[0].lexema, '## @ ~ " %')
        self.assertEqual(ts[0].tipo, 'COMENTARIO_LINEA')

    def test_cadena_sin_cerrar_recupera_siguiente_linea(self):
        l, ts = lex('"texto\nLUNES')
        self.assertEqual([(e.tipo, e.linea, e.columna) for e in l.errores.errores], [('CADENA_SIN_CERRAR', 1, 1)])
        self.assertEqual((ts[1].tipo, ts[1].linea), ('DIA', 2))

    def test_cadena_sin_cerrar_eof_y_escape_eof(self):
        for texto in ('"abc', '"abc\\'):
            l, _ = lex(texto)
            self.assertEqual(len(l.errores.errores), 1)
            self.assertEqual(l.errores.errores[0].tipo, 'CADENA_SIN_CERRAR')

    def test_escapes_y_salto_escapado(self):
        l, ts = lex('"a\\"b\\\\c\\n\\t\\\r\nd"')
        self.assertFalse(l.errores.errores)
        self.assertEqual(ts[0].valor, 'a"b\\c\n\td')
        self.assertEqual(ts[-1].linea, 2)

    def test_error_avanza_un_caracter_y_no_pierde_reservada(self):
        l, ts = lex('@%~# LUNES')
        self.assertEqual([e.columna for e in l.errores.errores], [1, 2, 3, 4])
        self.assertEqual(ts[-2].tipo, 'DIA')

    def test_bom_y_tab_stop(self):
        l, ts = lex('\ufeff\t\tLUNES\rMARTES')
        self.assertFalse(l.errores.errores)
        self.assertEqual((ts[0].linea, ts[0].columna, ts[0].inicio), (1, 9, 3))
        self.assertEqual((ts[1].linea, ts[1].columna), (2, 1))

    def test_palabra_completa_antes_de_reservada(self):
        l, ts = lex('LUNESextra HORARIO1 12-345')
        self.assertEqual(len(l.errores.errores), 3)
        self.assertFalse(any(t.tipo == 'DIA' for t in ts))

    def test_eof_idempotente(self):
        l, ts = lex('')
        self.assertEqual(ts[0].tipo, 'EOF')
        self.assertEqual(l.siguiente_token().tipo, 'EOF')

    def test_offsets_conservan_lexema(self):
        fuente = '##hola\r\n\t"mañana"\r\n@ 07:30'
        _, ts = lex(fuente)
        for t in ts:
            self.assertEqual(fuente[t.inicio:t.fin], t.lexema)

    def test_no_hay_tokenizadores_prohibidos(self):
        arbol = ast.parse((BASE / 'horarioscript/lexer.py').read_text(encoding='utf-8'))
        prohibidos = {'split', 'rsplit', 'find', 'rfind', 'partition', 'replace', 'isalpha', 'isdigit', 'isalnum', 'startswith', 'endswith'}
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                nombres = [a.name for a in nodo.names]
                self.assertFalse({'re', 'ply', 'regex'} & set(nombres))
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Attribute):
                self.assertNotIn(nodo.func.attr, prohibidos)


class PruebasEstructura(unittest.TestCase):
    def test_archivo_oficial(self):
        r = analizar(VALIDO)
        self.assertFalse(r.errores)
        self.assertFalse(r.choques)
        self.assertEqual(len(r.horario.clases), 2)
        self.assertGreaterEqual(len(r.frecuencias), 10)

    def test_todos_los_casos_entregables(self):
        for caso in json.loads((BASE / 'entrada/casos.json').read_text(encoding='utf-8')):
            with self.subTest(caso=caso['archivo']):
                r = analizar(leer_archivo(BASE / 'entrada' / caso['archivo']))
                obtenido = {'tipos_lexicos': [e.tipo for e in r.errores_lexicos], 'choques': len(r.choques), 'clases_validas': len(r.horario.clases)}
                self.assertEqual(obtenido, caso['esperado'])

    def test_atributos_en_otro_orden(self):
        r = analizar(VALIDO.replace('codigo: "LFP-0796", creditos: 4', 'creditos: 4, codigo: "LFP-0796"'))
        self.assertTrue(r.correcto)

    def test_referencias_invalidas_no_pasan_a_reportes(self):
        r = analizar(VALIDO.replace('con "DOC-001"', 'con "DOC-999"'))
        self.assertEqual([e.tipo for e in r.errores], ['REFERENCIA_INEXISTENTE'])
        self.assertEqual(len(r.horario.clases), 1)

    def test_seccion_opcional(self):
        r = analizar(VALIDO.replace(', seccion: "N"', '').replace(', seccion: "A"', ''))
        self.assertTrue(r.correcto)
        self.assertEqual({c.seccion for c in r.horario.clases}, {'SIN SECCION'})

    def test_secciones_duplicadas_y_ausentes(self):
        r = analizar('HORARIO { CURSOS {}; CURSOS {}; AULAS {}; CLASES {}; };')
        self.assertEqual({e.tipo for e in r.errores}, {'SECCION_DUPLICADA', 'SECCION_FALTANTE'})

    def test_codigo_duplicado(self):
        r = analizar(VALIDO.replace('codigo: "BD2-0812"', 'codigo: "LFP-0796"'))
        self.assertIn('CODIGO_DUPLICADO', [e.tipo for e in r.errores])
        self.assertEqual(len(r.horario.cursos), 1)

    def test_atributo_duplicado_y_faltante(self):
        for antes, despues, esperado in (('creditos: 4', 'creditos: 4, creditos: 3', 'ATRIBUTO_DUPLICADO'),
                                          (', creditos: 4', '', 'ATRIBUTO_FALTANTE')):
            with self.subTest(esperado=esperado):
                r = analizar(VALIDO.replace(antes, despues))
                self.assertIn(esperado, [e.tipo for e in r.errores])

    def test_intervalo_cero_o_invertido(self):
        for fin in ('07:00', '06:59'):
            r = analizar(VALIDO.replace('08:40', fin))
            self.assertIn('INTERVALO_INVALIDO', [e.tipo for e in r.errores])
            self.assertEqual(len(r.horario.clases), 1)

    def test_positivo_y_nombre_vacio(self):
        for antes, despues in (('creditos: 4', 'creditos: 0'), ('capacidad: 40', 'capacidad: 0'), ('"Otto Rodriguez"', '""')):
            r = analizar(VALIDO.replace(antes, despues))
            self.assertIn('VALOR_INVALIDO', [e.tipo for e in r.errores])

    def test_archivo_vacio_no_es_horario_valido(self):
        self.assertTrue(analizar('').errores)

    def test_lectura_extension_y_utf8(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / 'entrada.hor'
            ruta.write_bytes(b'\xef\xbb\xbfHORARIO\r\n')
            self.assertEqual(leer_archivo(ruta), 'HORARIO\r\n')
            with self.assertRaises(ValueError):
                leer_archivo(Path(carpeta) / 'entrada.txt')
            ruta.write_bytes(b'\xff')
            with self.assertRaises(UnicodeError):
                leer_archivo(ruta)


class PruebasHorarios(unittest.TestCase):
    def clase(self, numero, inicio, fin, docente='D-1', aula='A-1', dia='LUNES', seccion='B+'):
        return Clase(numero, 'C-1', docente, aula, dia, inicio, fin, seccion, Token(1, '', '', 1, 1))

    def test_intervalos_exhaustivos_con_oraculo_de_minutos(self):
        intervalos = [(a, b) for a in range(360, 365) for b in range(a+1, 367)]
        for (a, b), (c, d) in itertools.product(intervalos, repeat=2):
            esperado = bool(set(range(a, b)) & set(range(c, d)))
            cs = [self.clase(1, a, b), self.clase(2, c, d)]
            self.assertEqual(bool(detectar_choques(cs)), esperado)

    def test_motivos_sin_duplicar_pares(self):
        choque = detectar_choques([self.clase(1, 420, 600), self.clase(2, 450, 480)])[0]
        self.assertEqual(choque.motivos, ('CATEDRATICO', 'AULA'))
        self.assertEqual((choque.inicio, choque.fin), (450, 480))

    def test_mismo_tiempo_sin_recurso_compartido(self):
        self.assertFalse(detectar_choques([self.clase(1, 420, 480), self.clase(2, 420, 480, 'D-2', 'A-2')]))

    def test_dias_distintos(self):
        self.assertFalse(detectar_choques([self.clase(1, 420, 480), self.clase(2, 420, 480, dia='MARTES')]))

    def test_secciones_distintas_no_ocultan_choque(self):
        self.assertEqual(len(detectar_choques([self.clase(1, 420, 480), self.clase(2, 420, 480, seccion='A')])), 1)

    def test_tres_clases_tres_pares(self):
        self.assertEqual(len(detectar_choques([self.clase(i, 420, 480) for i in (1, 2, 3)])), 3)

    def test_niveles_fraccionarios(self):
        for minutos, nivel in ((0, 'BAJA'), (240, 'BAJA'), (241, 'NORMAL'), (600, 'NORMAL'), (601, 'ALTA'), (900, 'ALTA'), (901, 'SATURADA')):
            self.assertEqual(nivel_carga(minutos), nivel)

    def test_ocupacion_es_union_y_carga_es_suma(self):
        h = Horario(catedraticos={'D-1': Catedratico('D-1', 'Docente', 'TITULAR')}, aulas={'A-1': Aula('A-1', 20, 'T-1')},
                    clases=[self.clase(1, 420, 540), self.clase(2, 480, 600)])
        self.assertEqual(ocupaciones(h)[0]['minutos'], 180)
        self.assertEqual(cargas(h)[0]['minutos'], 240)
        self.assertEqual(cargas(h)[0]['cursos'], 1)
        self.assertEqual(cargas(h)[0]['secciones'], 1)

    def test_sugerencias_sin_colisiones(self):
        c = self.clase(1, 420, 480)
        h = Horario(clases=[c, self.clase(2, 360, 450)])
        opciones = sugerir_libres(h, c)
        self.assertEqual(len(opciones), 3)
        for dia, inicio, fin in opciones:
            self.assertEqual(fin - inicio, 60)
            self.assertGreaterEqual(inicio, 450)
            self.assertLessEqual(fin, 1260)


class PruebasReportes(unittest.TestCase):
    def test_reportes_autonomos_y_escape_html_dot(self):
        r = analizar(VALIDO.replace('Otto Rodriguez', '<script>alert(1)</script>'))
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = GeneradorReportes(r, carpeta, '<entrada>').generar()
            self.assertEqual(set(rutas), {'horario', 'carga', 'estadisticas', 'errores', 'dot'})
            for clave in ('horario', 'carga', 'estadisticas', 'errores'):
                texto = rutas[clave].read_text(encoding='utf-8')
                self.assertIn('<style>', texto)
                self.assertNotIn('<script>', texto)
                self.assertIn('&lt;entrada&gt;', texto)
            self.assertIn('&lt;script&gt;', rutas['horario'].read_text(encoding='utf-8'))

    def test_exportaciones_reproducen_tokens(self):
        r = analizar(VALIDO)
        with tempfile.TemporaryDirectory() as carpeta:
            for extension in ('json', 'csv'):
                ruta = Path(carpeta) / ('tokens.' + extension)
                exportar_tokens(r.tokens, ruta)
                if extension == 'json':
                    datos = json.loads(ruta.read_text(encoding='utf-8'))
                else:
                    with ruta.open(encoding='utf-8-sig', newline='') as f:
                        datos = list(csv.DictReader(f))
                self.assertEqual([d['lexema'] for d in datos], [t.lexema for t in r.tokens])

    def test_reportes_vacios_y_parciales(self):
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = GeneradorReportes(analizar(''), carpeta).generar()
            texto = rutas['estadisticas'].read_text(encoding='utf-8')
            self.assertIn('Resultados parciales', texto)
            self.assertIn('Sin asignaciones', texto)

    def test_choques_rojos_y_confirmados_verdes(self):
        r = analizar(leer_archivo(BASE / 'entrada/08_choque_docente.hor'))
        texto = GeneradorReportes(r, '.').semanal()
        self.assertIn('class="block conflict"', texto)
        self.assertIn('CONFIRMADO', texto)
        self.assertIn('CHOQUE DE HORARIO', texto)

    def test_ocupacion_mayor_a_80_roja(self):
        r = analizar(VALIDO)
        origen = r.horario.clases[0]
        r.horario.clases = [Clase(i+1, origen.curso, origen.catedratico, origen.aula, dia, 360, 1260, 'B+', origen.origen)
                            for i, dia in enumerate(('LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES'))]
        texto = GeneradorReportes(r, '.').estadisticas()
        self.assertIn('class="over"', texto)
        self.assertIn('83.33%', texto)


if __name__ == '__main__':
    unittest.main()
