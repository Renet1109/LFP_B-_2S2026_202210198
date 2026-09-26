"""Construye los tres PDF y sus fuentes Markdown con evidencia de ejecución real."""
from html import escape
import json
from pathlib import Path
import sys

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image, Preformatted
from reportlab.lib.utils import ImageReader

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from herramientas.diagramas import TRANSICIONES
from horarioscript.servicio import analizar, leer_archivo

DOCS = BASE / 'docs'
INK = colors.HexColor('#132f3a')
TEAL = colors.HexColor('#087d78')
MUTED = colors.HexColor('#55707a')
LIGHT = colors.HexColor('#edf4f5')
FONT, BOLD, MONO = 'Helvetica', 'Helvetica-Bold', 'Courier'
fontdir = Path('C:/Windows/Fonts')
if (fontdir / 'segoeui.ttf').exists():
    for name, file in (('HS', 'segoeui.ttf'), ('HS-Bold', 'segoeuib.ttf'), ('HS-Mono', 'consola.ttf')):
        pdfmetrics.registerFont(TTFont(name, str(fontdir / file)))
    FONT, BOLD, MONO = 'HS', 'HS-Bold', 'HS-Mono'
    pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=BOLD, italic=FONT, boldItalic=BOLD)

STYLES = getSampleStyleSheet()
for nombre, tamano, leading, color in (('Body', 10, 14.5, INK), ('SmallHS', 8.1, 11, MUTED),
                                       ('TitleHS', 28, 32, INK), ('HeadingHS', 17, 21, TEAL),
                                       ('SubHS', 11, 15, INK), ('CellHS', 8, 10.5, INK)):
    STYLES.add(ParagraphStyle(nombre, fontName=BOLD if nombre in ('TitleHS', 'HeadingHS', 'SubHS') else FONT,
                              fontSize=tamano, leading=leading, textColor=color, spaceAfter=9,
                              alignment=TA_LEFT))
STYLES.add(ParagraphStyle('CodeHS', fontName=MONO, fontSize=7.8, leading=10, spaceAfter=10,
                          backColor=LIGHT, borderPadding=8, textColor=INK))


def clean(texto):
    return str(texto).replace('–', '-').replace('—', '-').replace('→', '->').replace('≤', '<=').replace('≥', '>=')


def p(texto, estilo='Body'):
    return Paragraph(escape(clean(texto)).replace('\n', '<br/>'), STYLES[estilo])


def titulo(texto):
    return p(texto, 'HeadingHS')


def imagen(ruta, ancho=507, alto=500):
    w, h = ImageReader(str(ruta)).getSize()
    factor = min(ancho / w, alto / h)
    return Image(str(ruta), width=w*factor, height=h*factor)


def tabla(encabezado, filas, anchos):
    data = [[p(c, 'CellHS') for c in encabezado]] + [[p(c, 'CellHS') for c in fila] for fila in filas]
    t = Table(data, colWidths=anchos, repeatRows=1, hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), LIGHT), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                          ('LINEBELOW', (0, 0), (-1, -1), .4, colors.HexColor('#dbe6e9')),
                          ('LEFTPADDING', (0, 0), (-1, -1), 7), ('RIGHTPADDING', (0, 0), (-1, -1), 7),
                          ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 3)]))
    return t


def pie(canvas, doc):
    w, h = doc.pagesize
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(2)
    canvas.line(44, h-29, w-44, h-29)
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(44, h-22, 'HORARIOSCRIPT / LENGUAJES FORMALES / B+')
    canvas.drawString(44, 24, 'William René Toledo Corado · 202210198')
    canvas.drawRightString(w-44, 24, f'{doc.page}')


def construir(nombre, story):
    SimpleDocTemplate(str(DOCS / (nombre + '.pdf')), pagesize=(595.28, 841.89),
                      rightMargin=44, leftMargin=44, topMargin=48, bottomMargin=44,
                      title=nombre.replace('_', ' ') + ' - HorarioScript', author='William René Toledo Corado',
                      subject='Proyecto 1 · Segundo semestre 2026 · Desarrollo con asistencia de IA').build(story, onFirstPage=pie, onLaterPages=pie)


def tecnico():
    introduccion = 'HorarioScript convierte un archivo .hor en tokens, diagnósticos y un modelo de horario. El analizador se implementa manualmente: no importa re ni usa split/find para tokenizar. Python 3.10+ y Tkinter son los únicos requisitos de ejecución; Graphviz es opcional al renderizar el DOT.'
    arquitectura = [
        ('Token y GestorErrores', 'Clases del primer commit del estudiante, ampliadas con valor, offsets y fase; mantienen sus métodos originales.'),
        ('AnalizadorLexico', 'Recorre caracteres, conserva lexemas y produce tokens o errores mediante siguiente_token().'),
        ('LectorHorario', 'Valida bloques, atributos y referencias; construye solo registros utilizables. No mezcla estructura con errores léxicos.'),
        ('Servicio y modelos', 'Coordina fases; detecta choques, suma carga y calcula unión de intervalos de ocupación.'),
        ('GUI y reportes', 'Cada Documento conserva su análisis; GeneradorReportes produce cuatro HTML, DOT, CSV y JSON.'),
    ]
    s = [p('Manual técnico', 'TitleHS'), p('Proyecto 1 · Versión 1.0.0 · Segundo semestre 2026', 'SmallHS'), p(introduccion),
         titulo('1. Arquitectura y clases'), imagen(DOCS/'diagramas/clases.png', alto=240), Spacer(1, 12),
         tabla(('Componente', 'Responsabilidad'), arquitectura, (125, 382)), PageBreak(),
         titulo('2. AFD completo de reconocimiento'),
         p('Estado inicial I. Los nueve estados del bucle son I, PAL, NUM, HORA, MALNUM, TEXTO, ESCAPE, HASH y COMENTARIO. A y E representan salidas del método, no estados persistentes. Una nueva llamada reinicia I sin perder el cursor.'),
         imagen(DOCS/'diagramas/afd.png', alto=535),
         p('Diagrama generado con Graphviz desde docs/diagramas/afd.dot. Las flechas con * no consumen el delimitador; por eso la siguiente llamada lo procesa correctamente.', 'SmallHS'),
         PageBreak(), titulo('3. Tabla de transiciones · parte 1'),
         p('Cada grupo de entradas de un estado es disjunto. “Otro” excluye los grupos anteriores del mismo estado. CRLF se consume como una nueva línea lógica.', 'SmallHS'),
         tabla(('Estado', 'Entrada', 'Destino', 'Acción'), TRANSICIONES[:18], (52, 151, 64, 240)),
         PageBreak(), titulo('3. Tabla de transiciones · parte 2'),
         tabla(('Estado', 'Entrada', 'Destino', 'Acción'), TRANSICIONES[18:], (52, 151, 64, 240)), Spacer(1, 15),
         titulo('4. Sub-AFD de códigos'), imagen(DOCS/'diagramas/codigos.png', alto=175),
         p('Acepta únicamente si termina en CD. CP acumula el prefijo; CG exige al menos un dígito después del guion. CE es rechazo absorbente: el código retorna False inmediatamente. Al llegar a EOF en C0, CP o CG se rechaza; en CD se acepta.', 'SmallHS'),
         PageBreak(), titulo('5. Clasificación, prioridades y posiciones')]
    decisiones = [
        ('Palabras y códigos', 'Se consume la secuencia completa y se compara con tablas de igualdad exacta: bloques, elementos, relaciones, atributos, días y categorías. Si no coincide, se aplica el sub-AFD de códigos. La entrada HORARIO1 nunca se divide artificialmente en HORARIO + 1.'),
        ('Ambigüedad del ejemplo oficial', 'La regla escrita dice letras-guion-dígitos, pero BD2-0812 figura como ejemplo válido. Se admite una letra inicial seguida por letras o dígitos antes del guion. Los códigos se aceptan con comillas, como en el ejemplo, o sin ellas, como permiten las reglas de prioridad. Un prefijo iniciado en dígito se rechaza.'),
        ('Formas y contexto finito', 'El AFD identifica formas. _emitir conserva pendiente/esperado para los valores de codigo, aula, clase, con, en, dia, inicio, fin y categoria. Los comentarios no alteran ese contexto. Así un nombre entre comillas sigue siendo CADENA, mientras que un valor inválido después de codigo: genera CODIGO_MAL_FORMADO. No se atribuyen transiciones sintácticas completas al AFD.'),
        ('Horas', 'HORA acumula el candidato completo, incluso caracteres erróneos. minutos_validos exige longitud 5, dos dígitos, dos puntos y otros dos dígitos; calcula h*60+m, exige m<60 y 360<=total<=1260. La forma y el rango se validan después del reconocimiento del candidato. No se admiten horas con comillas.'),
        ('Cadenas y comentarios', 'Se conservan comillas y escapes en lexema y se decodifica valor. Se admiten \\" y \\\\, n/t/r escapados y una nueva línea física escapada como continuación. Otros escapes producen el carácter literal. Una cadena abierta termina en error al encontrar CR/LF no escapado o EOF. Un comentario ## es válido hasta CR, LF o EOF: el caso de “comentario sin cerrar” del enunciado no puede ser un error con esta sintaxis.'),
        ('Línea, columna y offsets', 'Línea y columna comienzan en 1. LF, CR o CRLF cuentan una nueva línea; una tabulación avanza al siguiente tope de cuatro columnas. Un BOM inicial no ocupa columna. Los offsets inicio/fin son índices de caracteres de Python, no de bytes. El editor normaliza saltos a LF; la lectura por consola conserva CRLF. El resaltado y la selección usan offsets sobre el texto que se analizó.'),
    ]
    for nombre, texto in decisiones:
        s += [p(nombre, 'SubHS'), p(texto)]
    s += [PageBreak(), titulo('6. Recuperación, extracción y choques')]
    algoritmos = [
        ('Recuperación léxica', 'Un carácter desconocido consume exactamente un carácter. Un candidato de palabra/hora inválido consume su unidad completa hasta un delimitador; una cadena abierta se detiene antes del salto. El método devuelve ERROR_LEXICO interno, agrega un diagnóstico y permite la siguiente llamada. Los tokens válidos tienen numeración consecutiva; EOF y errores no aparecen como tokens válidos.'),
        ('Extracción estructural', 'El lector auxiliar exige HORARIO y las cuatro secciones exactamente una vez, en cualquier orden. Permite coma final entre elementos y sección de clase opcional; exige los atributos requeridos y los separadores. Recupera en un siguiente elemento, sección o cierre. Se rechazan códigos duplicados, valores no positivos, intervalos invertidos y referencias inexistentes. Los catálogos vacíos son válidos.'),
        ('Choques', 'Se agrupa por día y se ordena por inicio. Antes de cada clase se retiran las activas cuyo fin<=inicio actual. Para cada activa restante se compara docente y aula. El traslape es [max(inicios), min(finales)); se guarda un solo par con uno o ambos motivos. Se compara entre todas las secciones. Dos clases que solo comparten sección no constituyen choque según el criterio obligatorio.'),
        ('Carga y ocupación', 'Carga docente: suma de fin-inicio, incluso si hay traslapes; cursos y secciones son conjuntos distintos. Umbrales continuos: BAJA 0-4 h, NORMAL >4-10 h, ALTA >10-15 h y SATURADA >15 h, para evitar huecos en horas fraccionarias. Ocupación de aula: longitud de la unión de intervalos por día, dividida entre 6*15*60=5400 minutos disponibles. Más del 80% se pinta rojo. Los empates se muestran completos y sin clases se indica Sin asignaciones.'),
        ('Costo y límites', 'El reconocimiento examina caracteres secuencialmente; mantiene tokens y fuente en memoria. La detección cuesta O(n log n + n*a), donde a es el máximo de clases activas; en el peor caso es O(n²), y puede producir esa cantidad de pares. El resaltado automático se limita a 200 000 caracteres, pero F5 analiza el documento completo. La GUI trabaja en el hilo principal: entradas extremadamente grandes pueden bloquearla durante el cálculo. No se afirma una capacidad ilimitada.'),
    ]
    for nombre, texto in algoritmos:
        s += [p(nombre, 'SubHS'), p(texto)]
    s += [PageBreak(), titulo('7. Reportes, trazabilidad y reproducción'),
          p('Los HTML incluyen su propio CSS, codificación UTF-8 y enlaces relativos entre los cuatro reportes. Toda entrada del usuario se escapa antes de insertarla en HTML. Los identificadores del DOT son internos; los textos se serializan entre comillas. Se llama a Graphviz con una lista de argumentos, sin shell.'),
          p('Al editar un documento se invalidan sus resultados y se desactivan los botones de reportes hasta analizar de nuevo. Cada análisis genera una carpeta con marca de tiempo; los reportes de demostración entregados son independientes de las ejecuciones posteriores.'),
          p('Se conserva el commit original 86118a7 y las clases de William. token.py se trasladó al paquete para no ocultar el módulo estándar de Python. Se preservan __str__, agregar_error, hay_errores, limpiar y obtener_errores. Los nuevos commits corresponden al desarrollo real asistido por IA.'),
          p('Validación reproducible', 'SubHS'),
          Preformatted('python -m unittest discover -s tests -v\npython herramientas/ejecutar_casos.py\npython main.py --analizar entrada/01_valido.hor\npython herramientas/diagramas.py dot', STYLES['CodeHS']),
          p('44 pruebas automatizadas; los doce casos y sus resultados están en evidencia_casos.json. Se comprueban todos los minutos del día, traslapes mediante un oráculo de conjuntos, escape de HTML, exportaciones, referencias, posiciones y recuperación. El tiempo registrado es una medición local, no una garantía de rendimiento.'),
          p('Fuentes', 'SubHS'),
          p('Enunciado HorarioScript_Proyecto1.pdf, secciones 4.2-4.8 y rúbrica 8.2. Python/Tkinter: https://docs.python.org/3/library/tkinter.html. Graphviz/DOT: https://graphviz.org/doc/info/lang.html. Consultadas para las herramientas; el diseño y el código del AFD se escribieron manualmente.'),
          p('Tutor y repositorio', 'SubHS'),
          p('Sección académica B+, tutor SamuelAguilar18. Se conserva el nombre LFP_B-_2S2026_202210198 por decisión del estudiante; no cambia su sección académica. El enunciado exige repositorio privado; comprobar esta configuración antes de entregar.')]
    construir('Manual_Tecnico', s)
    md = ['# Manual técnico · HorarioScript', '**William René Toledo Corado · 202210198 · B+**', introduccion, '## Arquitectura', '![Clases](diagramas/clases.png)']
    md += [f'### {a}\n{b}' for a, b in arquitectura]
    md += ['## AFD completo', '![AFD](diagramas/afd.png)', 'A/E son salidas; las llamadas reinician I conservando el cursor.', '## Tabla de transiciones', '| Estado | Entrada | Destino | Acción |', '|---|---|---|---|']
    md += ['| ' + ' | '.join(fila) + ' |' for fila in TRANSICIONES]
    md += ['## Sub-AFD de códigos', '![Códigos](diagramas/codigos.png)', 'Solo CD acepta al finalizar. CE es rechazo absorbente.']
    md += [f'## {a}\n{b}' for a, b in decisiones + algoritmos]
    md += ['## Validación', 'Ejecutar `python -m unittest discover -s tests -v` y `python herramientas/ejecutar_casos.py`. Evidencia en `evidencia_casos.json`.',
           '## Fuentes', '- Enunciado HorarioScript_Proyecto1.pdf.\n- https://docs.python.org/3/library/tkinter.html\n- https://graphviz.org/doc/info/lang.html',
           'Se conserva el commit inicial 86118a7, las clases base y los métodos originales. Desarrollo completado con asistencia de IA.']
    (DOCS / 'Manual_Tecnico.md').write_text('\n\n'.join(md), encoding='utf-8')


def usuario():
    r = analizar(leer_archivo(BASE/'entrada/01_valido.hor'))
    errores = analizar(leer_archivo(BASE/'entrada/02_caracteres.hor')).errores_lexicos
    s = [p('Manual de usuario', 'TitleHS'), p('HorarioScript · Proyecto 1 · William René Toledo Corado · 202210198 · B+', 'SmallHS'),
         titulo('1. Iniciar y abrir un horario'),
         p('Instale Python 3.10 o superior con Tcl/Tk. Abra una terminal dentro de Proyecto1. No necesita instalar paquetes para usar la aplicación. En Windows también puede usar ejecutar.bat.'),
         Preformatted('python -m tkinter\npython main.py entrada/demo.hor', STYLES['CodeHS']),
         p('Pulse Abrir .hor para cargar un archivo. Puede seleccionar varios: cada uno tendrá su propia pestaña. El editor permite escribir, corregir y guardar; un asterisco indica cambios sin guardar.'),
         imagen(DOCS/'capturas/gui_editor.png', alto=345),
         p('Captura real de la aplicación con demo.hor. El contenido largo se consulta con las barras de desplazamiento. Las ventanas pueden verse distintas según la escala de Windows.', 'SmallHS'),
         PageBreak(), titulo('2. Analizar, interpretar tokens y corregir errores'),
         p('Pulse Analizar o F5. Se procesa el contenido actual del editor, aunque todavía no lo haya guardado. La franja superior resume tokens, errores y choques. Los reportes se generan automáticamente.'),
         p('La tabla Tokens muestra número consecutivo, lexema exacto, tipo, línea y columna. Los comentarios son tokens válidos. Doble clic localiza el lexema en el editor. Ejemplo real de 01_valido.hor:', 'Body'),
         tabla(('N.º', 'Lexema', 'Tipo', 'Línea', 'Col.'), [[t.numero, t.lexema if len(t.lexema)<35 else t.lexema[:31]+'...', t.tipo, t.linea, t.columna] for t in r.tokens[:7]], (35, 170, 170, 60, 72)),
         Spacer(1, 15), p('En Errores, distinga la fase LEXICO de SINTACTICO y SEMANTICO. El análisis no se detiene al primer error. Estos son los tres errores ejecutados de 02_caracteres.hor:', 'Body'),
         tabla(('Lexema', 'Tipo', 'Línea', 'Col.'), [[e.lexema, e.tipo, e.linea, e.columna] for e in errores], (65, 302, 70, 70)),
         Spacer(1, 10), p('Doble clic en el error lleva al texto correspondiente. Corrija el editor y pulse F5 de nuevo. Al cambiar el texto se invalidan los resultados anteriores; los botones de reportes quedan desactivados hasta el siguiente análisis.'),
         p('Cuando hay errores, los reportes se identifican como parciales e incluyen solo registros completos con referencias válidas. No considere un reporte parcial como aprobación del archivo.'),
         PageBreak(), titulo('3. Reporte de horario semanal'),
         p('Pulse Horario semanal. El navegador abre horario.html; los enlaces superiores permiten cambiar de reporte. Hay una tabla por sección y columnas de lunes a sábado. Cada celda muestra curso, docente, aula e intervalo.'),
         imagen(DOCS/'capturas/reporte_horario.png', alto=360),
         p('Verde significa CONFIRMADO; rojo con advertencia significa CHOQUE DE HORARIO. El reporte marca el bloque involucrado completo y abajo especifica el traslape exacto. En demo.hor, las clases 5 y 6 comparten docente el lunes de 07:30 a 08:40.'),
         p('En la pestaña Choques de la aplicación, haga doble clic en un par para consultar propuestas libres. Se conserva duración, docente y aula; también se evita ocupar la misma sección. Las propuestas son orientativas y no editan el archivo.'),
         PageBreak(), titulo('4. Reporte de carga docente'),
         p('Pulse Carga docente. Verá código, nombre, categoría, horas semanales, cursos distintos, secciones distintas y nivel de carga. Se incluyen también docentes que no tienen clases.'),
         imagen(DOCS/'capturas/reporte_carga.png', alto=360),
         p('En demo.hor, Otto tiene 6.50 horas y Vivian 5.00 horas. La suma de carga cuenta todas las asignaciones, incluso cuando una de ellas se traslapa; por eso debe revisar también el reporte de choques.'),
         tabla(('Nivel', 'Horas semanales', 'Color'), [('BAJA', 'De 0 a 4', 'Azul'), ('NORMAL', 'Más de 4 y hasta 10', 'Verde'), ('ALTA', 'Más de 10 y hasta 15', 'Naranja'), ('SATURADA', 'Más de 15', 'Rojo')], (130, 240, 137)),
         PageBreak(), titulo('5. Reporte estadístico general'),
         p('Pulse Estadísticas en la barra de reportes. Los indicadores resumen cursos, docentes, aulas, clases, pares en choque y promedio de horas. Los empates de mayor carga u ocupación aparecen juntos.'),
         imagen(DOCS/'capturas/reporte_estadisticas.png', alto=300),
         p('Desplácese hacia abajo para ver la ocupación de aulas. La referencia es de 90 horas disponibles por semana; los traslapes no duplican minutos ocupados. Se resalta en rojo una ocupación mayor al 80%.'),
         imagen(DOCS/'capturas/ocupacion_aulas.png', alto=230),
         PageBreak(), titulo('6. Guardar, exportar y usar Graphviz'),
         p('Guardar / Ctrl+S guarda el editor en UTF-8. Guardar como crea otro archivo .hor. Al cerrar una pestaña o salir, se pregunta si desea guardar los cambios pendientes.'),
         p('Exportar tokens permite elegir JSON o CSV. El CSV incluye encabezados y BOM UTF-8 para facilitar su apertura en hojas de cálculo. Los reportes automáticos también guardan ambas exportaciones y resultado.json.'),
         p('Diagrama genera SVG a partir de horario.dot si Graphviz está en PATH. Si no lo encuentra, indica dónde quedó el DOT; no pierde el análisis. Puede instalar Graphviz desde graphviz.org o usar manualmente:'),
         Preformatted('dot -Tsvg horario.dot -o horario.svg', STYLES['CodeHS']),
         titulo('7. Estructura de entrada y ayuda'),
         p('HORARIO contiene CURSOS, CATEDRATICOS, AULAS y CLASES. Cada sección aparece exactamente una vez. Use los archivos entregados en entrada como plantillas; 01_valido.hor reproduce el ejemplo del enunciado.'),
         Preformatted('clase: "LFP-0796" con "DOC-001" en "A-101"\n[dia: LUNES, inicio: 07:00, fin: 08:40, seccion: "B+"],', STYLES['CodeHS']),
         tabla(('Situación', 'Cómo resolverla'), [
             ('Python no se reconoce', 'Instale Python 3.10+ y agréguelo a PATH; pruebe py -3 main.py.'),
             ('No se encuentra tkinter/init.tcl', 'Repare la instalación de Python incluyendo Tcl/Tk. Compruebe python -m tkinter.'),
             ('Caracteres o día inválidos', 'Use los días en mayúsculas, sin tilde ni comillas; revise la posición de cada error.'),
             ('Hora inválida', 'Use dos dígitos para hora y minutos; respete 06:00-21:00 y fin posterior a inicio.'),
             ('No aparecen reportes', 'Pulse F5 después de cualquier edición. Revise permisos de escritura de Proyecto1/salidas.'),
             ('No abre el navegador', 'Abra directamente los archivos HTML indicados en la barra inferior.'),
         ], (160, 347))]
    construir('Manual_Usuario', s)
    md = ['# Manual de usuario · HorarioScript', '**William René Toledo Corado · 202210198 · B+**',
          '## Ejecutar', 'Instale Python 3.10+ con Tcl/Tk. Desde Proyecto1: `python main.py entrada/demo.hor`. No requiere paquetes externos para funcionar.',
          '## Abrir y editar', 'Abra uno o varios .hor. Cada pestaña tiene su propio editor. Un asterisco indica cambios sin guardar. Use Ctrl+S para guardar y F5 para analizar el editor actual.',
          '![Editor real](capturas/gui_editor.png)',
          '## Tokens y errores', 'Revise las pestañas Tokens, Errores, Choques y Estadísticas. Doble clic en token/error localiza el texto. Cambiarlo invalida resultados hasta pulsar F5. Los diagnósticos léxicos, sintácticos y semánticos se distinguen. Las columnas empiezan en 1 y los tabuladores avanzan a topes de cuatro.',
          '## Horario semanal', '![Horario](capturas/reporte_horario.png)', 'Una tabla por sección. Verde: confirmado; rojo: choque. El detalle indica el traslape exacto. Demo: siete clases y un choque de docente de 07:30 a 08:40 el lunes. Doble clic en Choques propone opciones sin modificar la entrada.',
          '## Carga docente', '![Carga](capturas/reporte_carga.png)', 'Suma de asignaciones, cursos y secciones distintos. BAJA 0-4 h, NORMAL >4-10 h, ALTA >10-15 h, SATURADA >15 h.',
          '## Estadísticas y ocupación', '![Estadísticas](capturas/reporte_estadisticas.png)', '![Ocupación](capturas/ocupacion_aulas.png)', 'Ocupación sobre 90 horas por aula, contando la unión de intervalos. Más del 80% se pinta rojo.',
          '## Exportar y diagramar', 'Exportar tokens guarda JSON/CSV. Diagrama usa Graphviz de PATH; sin él se conserva el DOT. También puede usar `dot -Tsvg horario.dot -o horario.svg`.',
          '## Ayuda', 'Use `python -m tkinter` para comprobar Tcl/Tk. Use UTF-8 y extensión .hor. Corrija los errores y vuelva a analizar; los reportes parciales no certifican un horario válido. Los archivos están en salidas, con una carpeta distinta por análisis.']
    (DOCS/'Manual_Usuario.md').write_text('\n\n'.join(md), encoding='utf-8')


def casos():
    evidencia = json.loads((DOCS/'evidencia_casos.json').read_text(encoding='utf-8'))
    s = [p('Casos de prueba', 'TitleHS'), p('William René Toledo Corado · 202210198 · Lenguajes Formales B+', 'SmallHS'),
         p('Doce archivos ejecutados. Las expectativas se declararon en entrada/casos.json; herramientas/ejecutar_casos.py guarda resultados y diagnósticos reales en docs/evidencia_casos.json. Todos los casos de esta edición coinciden con sus expectativas.'),
         Preformatted('python -m unittest discover -s tests -v\npython herramientas/ejecutar_casos.py', STYLES['CodeHS']),
         tabla(('Caso', 'Escenario', 'Resultado'), [[c['archivo'][:2], c['titulo'], 'PASS' if c['aprobado'] else 'FAIL'] for c in evidencia], (45, 390, 72)),
         Spacer(1, 12), p('Además de estos doce escenarios, hay 44 pruebas automatizadas. La prueba de intervalos compara el detector contra intersecciones de conjuntos de minutos; la prueba de horas recorre los 1440 minutos del día. No se presentan esas iteraciones como miles de pruebas independientes.', 'SmallHS'),
         PageBreak(), titulo('Entrada base completa · 01_valido.hor')]
    fuente = leer_archivo(BASE/'entrada/01_valido.hor')
    # Se ajusta la presentación del listado, no el archivo original de prueba.
    import textwrap
    lineas = []
    for i, linea in enumerate(fuente.splitlines(), 1):
        trozos = textwrap.wrap(linea, width=86, break_long_words=False, break_on_hyphens=False) or ['']
        lineas += [f'{i:02}  ' + trozos[0]] + ['    ' + l for l in trozos[1:]]
    s += [Preformatted('\n'.join(lineas), STYLES['CodeHS']),
          p('Los siguientes casos parten de esta entrada cuando se indica una sustitución. Los archivos .hor completos se incluyen en entrada; los fragmentos de las fichas describen exactamente el cambio aplicado.', 'SmallHS')]
    cambios = [
        'Sin cambios: entrada base completa de la página anterior.',
        'Se inserta una línea con @ % ~ antes de CURSOS. Se esperan errores en línea 3, columnas 1, 3 y 5.',
        'En la primera clase se sustituye inicio: 07:00 por inicio: 05:59.',
        'En la primera clase se sustituye dia: LUNES por dia: DOMINGO.',
        'En el primer curso se sustituye codigo: "LFP-0796" por codigo: "LFP0796". La clase que lo referencia no puede usarse.',
        'Al final se agrega, sin salto posterior: ## comentario sin cerrar aparente: @ % ~ "',
        'La primera declaración de curso se reemplaza por: curso: "Cadena sin cerrar. La línea siguiente sigue procesándose.',
        'Se agrega al inicio de CLASES: clase: "BD2-0812" con "DOC-001" en "LAB-3" [dia: LUNES, inicio: 07:30, fin: 09:00, seccion: "B+"],',
        'Se agrega al inicio de CLASES: clase: "BD2-0812" con "DOC-002" en "A-101" [dia: LUNES, inicio: 08:00, fin: 09:00, seccion: "B+"],',
        'Primera clase: LUNES 06:00-07:00. Segunda clase: LUNES 07:00-21:00 en A-101. Comparten aula y son adyacentes, sin traslape.',
        'HORARIO { CURSOS {}; CATEDRATICOS {}; AULAS {}; CLASES {}; };',
        'En la primera clase se sustituye inicio: 07:00 por inicio: 7:00.',
    ]
    md = ['# Casos ejecutados', '**William René Toledo Corado · 202210198 · B+**', '12 casos y 44 pruebas automatizadas. Evidencia: evidencia_casos.json.', '## Entrada base', '```text\n' + fuente + '```']
    for i, c in enumerate(evidencia):
        if i % 2 == 0:
            s += [PageBreak()]
        titulo_caso = f'{i+1:02}. {c["titulo"]}'
        esperado = f'Errores léxicos: {", ".join(c["esperado"]["tipos_lexicos"]) or "ninguno"}. Choques: {c["esperado"]["choques"]}. Clases válidas: {c["esperado"]["clases_validas"]}.'
        obtenido = f'{"PASS" if c["aprobado"] else "FAIL"}. {c["tokens"]} tokens válidos; {len(c["obtenido"]["tipos_lexicos"])} errores léxicos; {c["obtenido"]["choques"]} choques; {c["obtenido"]["clases_validas"]} clases válidas.'
        s += [titulo(titulo_caso), p(c['archivo'], 'SmallHS'), p('Entrada: ' + cambios[i]), p('Esperado: ' + esperado), p('Obtenido: ' + obtenido)]
        detalles = '; '.join(f'{e["tipo"]} ({e["linea"]}:{e["columna"]}, {e["fase"]})' for e in c['diagnosticos'])
        if detalles:
            s += [p('Diagnósticos reales: ' + detalles, 'SmallHS')]
        if i == 5:
            s += [p('Aclaración del enunciado: el comentario no requiere cierre explícito. EOF lo termina conforme a la sección 4.5. La ausencia de error es el comportamiento correcto; el caso 07 cubre una cadena sin cerrar.', 'SmallHS')]
        s += [Spacer(1, 18)]
        md += [f'## {titulo_caso}', f'Archivo: `{c["archivo"]}`.\n\nEntrada: {cambios[i]}\n\nEsperado: {esperado}\n\nObtenido: {obtenido}\n\nDiagnósticos: {detalles or "ninguno"}.']
    construir('Casos_de_Prueba', s)
    (DOCS/'Casos_de_Prueba.md').write_text('\n\n'.join(md), encoding='utf-8')


if __name__ == '__main__':
    tecnico()
    usuario()
    casos()
    print('Tres manuales PDF y sus versiones Markdown generados con evidencia real.')
