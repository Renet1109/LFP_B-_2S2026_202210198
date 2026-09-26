"""Reportes HTML autónomos, DOT y exportaciones; nunca ejecuta contenido de la entrada."""
import csv
import json
import shutil
import subprocess
from html import escape
from pathlib import Path

from .lexer import DIAS
from .servicio import cargas, hora, ocupaciones, sugerir_libres


CSS = """
:root{--ink:#132f3a;--muted:#55707a;--line:#dbe6e9;--teal:#087d78;--bg:#f2f6f7}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,Segoe UI,sans-serif}
header{background:#132f3a;color:white;padding:27px max(24px,calc((100vw - 1440px)/2));border-bottom:5px solid #36c7ac}
header p{margin:4px 0 0;color:#c9dedf}.brand{font-size:13px;letter-spacing:2px;color:#64dcc8;text-transform:uppercase}
h1{font-size:30px;line-height:1.2;margin:10px 0}h2{font-size:21px;margin:0 0 16px}h3{font-size:17px}
nav{display:flex;gap:8px;flex-wrap:wrap;margin-top:18px}nav a{color:white;text-decoration:none;border:1px solid #66828a;border-radius:7px;padding:7px 13px}nav a:hover{background:#28525c}
main{max-width:1488px;margin:auto;padding:24px}section,.card{background:white;border:1px solid var(--line);border-radius:12px;padding:22px;margin:0 0 22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(155px,1fr));gap:14px;margin-bottom:22px}.kpis .card{margin:0}.number{font-size:32px;font-weight:700;line-height:1.25}.label{color:var(--muted);font-size:13px}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:12px}th{background:#edf4f5;color:#284b57;font-size:12px;letter-spacing:.4px}tbody tr:last-child td{border-bottom:0}
.agenda{table-layout:fixed;min-width:950px}.agenda th:first-child{width:105px}.agenda td{border:1px solid var(--line);padding:7px}.agenda th{border:1px solid var(--line)}.time{font-weight:600;white-space:nowrap}
.block{background:#e7f5ed;border-left:4px solid #269763;border-radius:5px;padding:9px;margin-bottom:7px;font-size:12px;overflow-wrap:anywhere}.block:last-child{margin-bottom:0}.block strong{display:block;font-size:13px}.block.conflict{background:#ffe7e7;border-color:#c63838}.state{font-weight:750;font-size:10px;margin-top:6px;display:block;color:#226944}.conflict .state{color:#aa2525}
.badge{display:inline-block;border-radius:30px;padding:4px 10px;font-size:11px;font-weight:700}.BAJA{background:#e0efff;color:#125393}.NORMAL{background:#dff3e8;color:#176541}.ALTA{background:#fff0d7;color:#925000}.SATURADA{background:#ffe1e1;color:#a72222}
.warning{padding:15px 18px;border:1px solid #efc987;border-left:5px solid #b47b11;background:#fff7e7;border-radius:8px;margin-bottom:20px}.good{background:#e7f5ed;border-color:#95c8ac;border-left-color:#269763}.muted{color:var(--muted)}.legend{display:flex;gap:18px;margin-bottom:16px;font-size:13px}.legend span{padding:5px 10px;border-radius:6px}.empty{color:#8fa3aa;text-align:center}.bar{height:9px;background:#e4edef;border-radius:10px;overflow:hidden;min-width:130px;margin-top:6px}.bar i{display:block;height:100%;background:#159389}.over{background:#fff0f0}.over .bar i{background:#c63838}
code,pre{font-family:Consolas,monospace}code{white-space:pre-wrap;overflow-wrap:anywhere}footer{max-width:1488px;margin:auto;padding:0 24px 28px;color:var(--muted);font-size:12px}a{color:#087d78}.description{max-width:900px}details{margin-top:15px}summary{cursor:pointer;color:var(--teal)}
@media(max-width:650px){main{padding:12px}section{padding:14px}h1{font-size:25px}header{padding:22px 18px}th,td{padding:9px}}
@media print{nav{display:none}body{background:white}header{background:white;color:#132f3a;padding:10px}header p{color:#55707a}main{padding:0}section{break-inside:avoid}table{font-size:10px}.agenda{min-width:0}.block{font-size:9px}.block strong{font-size:10px}}
"""


def h(valor):
    return escape(str(valor), quote=True)


def tabla(encabezados, filas):
    return ('<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{h(t)}</th>' for t in encabezados)
            + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in fila) + '</tr>' for fila in filas)
            + '</tbody></table></div>')


class GeneradorReportes:
    def __init__(self, resultado, carpeta, nombre="Horario académico"):
        self.resultado = resultado
        self.horario = resultado.horario
        self.carpeta = Path(carpeta)
        self.nombre = nombre
        self.en_choque = {n for c in resultado.choques for n in (c.primera, c.segunda)}

    def pagina(self, titulo, contenido):
        advertencia = ""
        if self.resultado.errores:
            advertencia = (f'<div class="warning"><strong>Resultados parciales.</strong> Hay {len(self.resultado.errores)} diagnósticos. '
                           'Solo se incluyen registros completos y clases con referencias válidas. '
                           '<a href="errores.html">Revise los errores antes de usar el horario.</a></div>')
        return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<title>{h(titulo)} · HorarioScript</title><style>{CSS}</style></head><body><header>'
                f'<div class="brand">HorarioScript / Ciclo 2026</div><h1>{h(titulo)}</h1><p>{h(self.nombre)}</p>'
                '<nav aria-label="Reportes"><a href="horario.html">Horario semanal</a><a href="carga.html">Carga docente</a>'
                '<a href="estadisticas.html">Estadísticas</a><a href="errores.html">Diagnósticos</a></nav></header>'
                f'<main>{advertencia}{contenido}</main><footer>William René Toledo Corado · 202210198 · LFP B+ · '
                'Python y AFD manual. Archivos HTML autónomos, sin servicios externos.</footer></body></html>')

    def generar(self):
        self.carpeta.mkdir(parents=True, exist_ok=True)
        rutas = {}
        for clave, titulo, contenido in (("horario", "Horario semanal", self.semanal()),
                                         ("carga", "Carga de catedráticos", self.carga()),
                                         ("estadisticas", "Estadístico general del ciclo", self.estadisticas()),
                                         ("errores", "Diagnósticos del análisis", self.errores())):
            rutas[clave] = self.carpeta / f"{clave}.html"
            rutas[clave].write_text(self.pagina(titulo, contenido), encoding="utf-8")
        rutas["dot"] = self.carpeta / "horario.dot"
        rutas["dot"].write_text(self.dot(), encoding="utf-8")
        exportar_tokens(self.resultado.tokens, self.carpeta / "tokens.json")
        exportar_tokens(self.resultado.tokens, self.carpeta / "tokens.csv")
        resumen = {"tokens": len(self.resultado.tokens), "errores_lexicos": len(self.resultado.errores_lexicos),
                   "diagnosticos": [vars(e) for e in self.resultado.errores], "choques": [vars(c) for c in self.resultado.choques],
                   "milisegundos": self.resultado.milisegundos, "frecuencias": self.resultado.frecuencias}
        (self.carpeta / "resultado.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
        return rutas

    def semanal(self):
        contenido = ('<div class="legend"><span class="NORMAL">CONFIRMADO</span><span class="SATURADA">⚠ CHOQUE DE HORARIO</span></div>')
        secciones = sorted({c.seccion for c in self.horario.clases}) or ["SIN SECCION"]
        for seccion in secciones:
            clases = [c for c in self.horario.clases if c.seccion == seccion]
            limites = sorted({360, 1260} | {x for c in clases for x in (c.inicio, c.fin)})
            contenido += f'<section><h2>Sección {h(seccion)}</h2><div class="scroll"><table class="agenda"><thead><tr><th>HORA</th>'
            contenido += ''.join(f'<th>{d}</th>' for d in DIAS) + '</tr></thead><tbody>'
            for inicio, fin in zip(limites, limites[1:]):
                contenido += f'<tr><td class="time">{hora(inicio)}<br>{hora(fin)}</td>'
                for dia in DIAS:
                    celdas = ""
                    for clase in clases:
                        if clase.dia == dia and clase.inicio < fin and inicio < clase.fin:
                            choque = clase.numero in self.en_choque
                            celdas += (f'<div class="block{" conflict" if choque else ""}"><strong>{h(self.horario.cursos[clase.curso].nombre)}</strong>'
                                       f'{h(self.horario.catedraticos[clase.catedratico].nombre)}<br>Aula {h(clase.aula)} · #{clase.numero}<br>'
                                       f'{hora(clase.inicio)}–{hora(clase.fin)}<span class="state">'
                                       f'{"⚠ CHOQUE DE HORARIO" if choque else "CONFIRMADO"}</span></div>')
                    contenido += f'<td>{celdas or "<div class=empty>—</div>"}</td>'
                contenido += '</tr>'
            contenido += '</tbody></table></div><p class="muted">Las filas se dividen en los límites reales de las clases; cada bloque conserva su intervalo completo.</p></section>'
        if self.resultado.choques:
            filas = [[f'#{c.primera} / #{c.segunda}', c.dia, f'{hora(c.inicio)}–{hora(c.fin)}', h(' y '.join(c.motivos))] for c in self.resultado.choques]
            contenido += '<section><h2>Choques detectados</h2>' + tabla(("Clases", "Día", "Traslape", "Recurso compartido"), filas)
            contenido += '<details><summary>Propuestas de reprogramación</summary><p>Opciones orientativas; no modifican la entrada. Conservan docente, aula y duración, y evitan clases de la misma sección.</p><ul>'
            for clase in self.horario.clases:
                if clase.numero in self.en_choque:
                    opciones = sugerir_libres(self.horario, clase)
                    contenido += f'<li>Clase #{clase.numero}: ' + h('; '.join(f'{d} {hora(i)}–{hora(f)}' for d, i, f in opciones) or 'No hay opciones disponibles') + '</li>'
            contenido += '</ul></details></section>'
        else:
            contenido += '<div class="warning good">No se detectaron choques entre las clases válidas.</div>'
        return contenido

    def carga(self):
        filas = []
        for c in cargas(self.horario):
            d = c["docente"]
            filas.append([f'<strong>{h(d.nombre)}</strong><br><span class="muted">{h(d.codigo)}</span>', h(d.categoria),
                          f'{c["minutos"] / 60:.2f} h', str(c["cursos"]), str(c["secciones"]), f'<span class="badge {c["nivel"]}">{c["nivel"]}</span>'])
        return ('<section><h2>Distribución de la carga semanal</h2><p class="description muted">Se suman las duraciones asignadas, incluso si se traslapan. '
                'Los cursos y las secciones se cuentan sin duplicados. Se incluyen docentes sin clases.</p>'
                + tabla(("Catedrático", "Categoría", "Horas semanales", "Cursos", "Secciones", "Carga"), filas)
                + '<p class="muted">BAJA: 0–4 h · NORMAL: más de 4 y hasta 10 h · ALTA: más de 10 y hasta 15 h · SATURADA: más de 15 h.</p></section>')

    def estadisticas(self):
        docentes, aulas = cargas(self.horario), ocupaciones(self.horario)
        total = sum(c["minutos"] for c in docentes)
        media = total / 60 / len(docentes) if docentes else 0
        cards = [(len(self.horario.cursos), "Cursos"), (len(docentes), "Catedráticos"), (len(aulas), "Aulas"),
                 (len(self.horario.clases), "Clases válidas"), (len(self.resultado.choques), "Pares en choque"), (f'{media:.2f} h', "Promedio por docente")]
        contenido = '<div class="kpis">' + ''.join(f'<div class="card"><div class="number">{v}</div><div class="label">{n}</div></div>' for v, n in cards) + '</div>'
        mayor_carga = max((c["minutos"] for c in docentes), default=0)
        mayor_aula = max((c["minutos"] for c in aulas), default=0)
        nombres = ', '.join(c["docente"].nombre for c in docentes if c["minutos"] == mayor_carga) if mayor_carga else "Sin asignaciones"
        codigos = ', '.join(c["aula"].codigo for c in aulas if c["minutos"] == mayor_aula) if mayor_aula else "Sin asignaciones"
        contenido += f'<section><h2>Asignaciones destacadas</h2><p><strong>Mayor carga docente:</strong> {h(nombres)} ({mayor_carga/60:.2f} h).</p><p><strong>Mayor ocupación de aula:</strong> {h(codigos)} ({mayor_aula/60:.2f} h).</p></section>'
        contenido += '<section><h2>Ocupación semanal de aulas</h2><p class="description muted">Disponibilidad: 90 horas por aula (lunes a sábado, 06:00–21:00). '
        contenido += 'Se cuenta la unión de los intervalos ocupados; un traslape no duplica la ocupación. El rojo señala más del 80%.</p><div class="scroll"><table><thead><tr><th>Aula / edificio</th><th>Capacidad</th><th>Clases</th><th>Horas ocupadas</th><th>Ocupación</th></tr></thead><tbody>'
        for a in aulas:
            aula = a["aula"]
            contenido += (f'<tr class="{"over" if a["porcentaje"] > 80 else ""}"><td><strong>{h(aula.codigo)}</strong><br>{h(aula.edificio)}</td><td>{aula.capacidad}</td>'
                          f'<td>{a["clases"]}</td><td>{a["minutos"]/60:.2f} h</td><td>{a["porcentaje"]:.2f}%<div class="bar"><i style="width:{a["porcentaje"]:.3f}%"></i></div></td></tr>')
        return contenido + '</tbody></table></div></section>'

    def errores(self):
        contenido = '<section><h2>Errores y recuperación</h2><p>La posición señala el inicio del lexema. Las columnas comienzan en 1; cada tabulación avanza al siguiente tope de 4 columnas.</p>'
        for fase, nombre in (("LEXICO", "Errores léxicos"), ("SINTACTICO", "Estructura del archivo"), ("SEMANTICO", "Consistencia de los datos")):
            errores = [e for e in self.resultado.errores if e.fase == fase]
            contenido += f'<h3>{nombre} ({len(errores)})</h3>'
            if errores:
                contenido += tabla(("N.º", "Lexema", "Tipo", "Descripción", "Línea", "Columna"),
                                   [[str(e.numero), f'<code>{h(e.lexema)}</code>', h(e.tipo), h(e.descripcion), str(e.linea), str(e.columna)] for e in errores])
            else:
                contenido += '<p class="muted">Sin errores en esta fase.</p>'
        return contenido + '</section>'

    def dot(self):
        q = lambda s: json.dumps(str(s), ensure_ascii=False)
        lineas = ['digraph Horario {', 'rankdir=LR;', 'graph [fontname="Arial", bgcolor="#f6f9fa"];',
                  'node [fontname="Arial", shape=box, style="rounded,filled", fillcolor="#e5f3f0"];',
                  'edge [fontname="Arial", color="#66828a"];', 'raiz [label="HORARIO", fillcolor="#9ddfcd"];']
        indices = {}
        for tipo, catalogo in (("curso", self.horario.cursos), ("docente", self.horario.catedraticos), ("aula", self.horario.aulas)):
            lineas += [f'{tipo}s [label={q(tipo.upper() + "S")}];', f'raiz -> {tipo}s;']
            for i, objeto in enumerate(catalogo.values()):
                nodo = f'{tipo}{i}'
                indices[(tipo, objeto.codigo)] = nodo
                etiqueta = objeto.codigo + ("\n" + objeto.nombre if hasattr(objeto, "nombre") else "\n" + objeto.edificio)
                lineas += [f'{nodo} [label={q(etiqueta)}];', f'{tipo}s -> {nodo};']
        lineas += ['clases [label="CLASES"];', 'raiz -> clases;']
        for c in self.horario.clases:
            etiqueta = f'Clase #{c.numero} · {c.seccion}\n{c.dia} {hora(c.inicio)}-{hora(c.fin)}'
            color = '#ffd9d9' if c.numero in self.en_choque else '#dff3e8'
            lineas += [f'clase{c.numero} [label={q(etiqueta)}, fillcolor="{color}"];', f'clases -> clase{c.numero};']
            for tipo, codigo, relacion in (("curso", c.curso, "curso"), ("docente", c.catedratico, "con"), ("aula", c.aula, "en")):
                lineas.append(f'clase{c.numero} -> {indices[(tipo, codigo)]} [label={q(relacion)}];')
        return '\n'.join(lineas + ['}'])


def exportar_tokens(tokens, ruta):
    ruta = Path(ruta)
    campos = ("numero", "lexema", "tipo", "linea", "columna")
    datos = [{c: getattr(t, c) for c in campos} for t in tokens]
    if ruta.suffix.lower() == ".csv":
        with ruta.open("w", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            escritor.writeheader()
            escritor.writerows(datos)
    elif ruta.suffix.lower() == ".json":
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        raise ValueError("La exportación debe ser .csv o .json")


def renderizar_dot(ruta, ejecutable=None):
    ruta = Path(ruta)
    dot = str(ejecutable) if ejecutable else shutil.which("dot")
    if not dot:
        raise FileNotFoundError("Graphviz no está en PATH. El archivo DOT sí fue generado; puede renderizarlo después.")
    destino = ruta.with_suffix(".svg")
    subprocess.run([dot, "-Tsvg", str(ruta), "-o", str(destino)], check=True, capture_output=True, timeout=30)
    return destino
