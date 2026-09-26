"""Aplicación Tkinter: documentos independientes y resultados asociados al editor activo."""
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, font
import webbrowser

from .lexer import AnalizadorLexico
from .reportes import GeneradorReportes, exportar_tokens, renderizar_dot
from .servicio import analizar, hora, leer_archivo, sugerir_libres

BASE = Path(__file__).resolve().parent.parent


class Documento(ttk.Frame):
    def __init__(self, parent, app, nombre="Sin título", ruta=None, contenido=""):
        super().__init__(parent)
        self.app, self.nombre, self.ruta = app, nombre, ruta
        self.resultado, self.rutas = None, {}
        self.modificado = False
        self.timer = None
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.texto = tk.Text(self, undo=True, wrap="none", font=("Consolas", 11),
                             background="#f9fbfc", foreground="#183944", insertbackground="#087d78",
                             padx=15, pady=12, borderwidth=0)
        self.texto.configure(tabs=(font.Font(font=self.texto["font"]).measure("    "),))
        self.texto.grid(row=0, column=0, sticky="nsew")
        sy = ttk.Scrollbar(self, orient="vertical", command=self.texto.yview)
        sx = ttk.Scrollbar(self, orient="horizontal", command=self.texto.xview)
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        self.texto.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.texto.tag_configure("reservada", foreground="#1262a3", font=("Consolas", 11, "bold"))
        self.texto.tag_configure("literal", foreground="#a44e24")
        self.texto.tag_configure("comentario", foreground="#64806d")
        self.texto.tag_configure("error", background="#ffe0df", underline=True)
        self.texto.tag_configure("destino", background="#ffe1a7")
        self.texto.insert("1.0", contenido.replace("\r\n", "\n").replace("\r", "\n"))
        self.texto.edit_modified(False)
        self.texto.bind("<<Modified>>", self.cambio)
        self.texto.bind("<KeyRelease>", lambda _e: self.app.actualizar_cursor())
        self.texto.bind("<ButtonRelease>", lambda _e: self.app.actualizar_cursor())
        self.resaltar()

    def fuente(self):
        return self.texto.get("1.0", "end-1c")

    def cambio(self, _event=None):
        if not self.texto.edit_modified():
            return
        self.texto.edit_modified(False)
        self.modificado = True
        self.resultado, self.rutas = None, {}
        self.app.documentos.tab(self, text=self.nombre + " *")
        self.app.mostrar_resultado()
        if self.timer is not None:
            self.after_cancel(self.timer)
        self.timer = self.after(350, self.resaltar)

    def resaltar(self):
        self.timer = None
        for tag in ("reservada", "literal", "comentario", "error", "destino"):
            self.texto.tag_remove(tag, "1.0", "end")
        fuente = self.fuente()
        # La misma lógica del AFD se reutiliza: el resaltado no crea un segundo lexer.
        if len(fuente) > 200000:
            return
        for token in AnalizadorLexico(fuente).analizar():
            if token.tipo == "EOF":
                continue
            if token.tipo in ("RESERVADA_BLOQUE", "RESERVADA_ELEMENTO", "RESERVADA_RELACION", "ATRIBUTO", "DIA", "CATEGORIA"):
                tag = "reservada"
            elif token.tipo == "COMENTARIO_LINEA":
                tag = "comentario"
            elif token.tipo == "ERROR_LEXICO":
                tag = "error"
            else:
                tag = "literal"
            self.texto.tag_add(tag, f"1.0+{token.inicio}c", f"1.0+{token.fin}c")


class HorarioScriptApp(tk.Tk):
    def __init__(self, ruta_inicial=None):
        super().__init__()
        self.title("HorarioScript · William Toledo · 202210198 · B+")
        self.geometry("1280x720")
        self.minsize(1050, 700)
        self.configure(background="#eef4f5")
        self.protocol("WM_DELETE_WINDOW", self.salir)
        self.estilo()
        self.crear_interfaz()
        self.bind("<Control-o>", lambda _e: self.abrir())
        self.bind("<Control-s>", lambda _e: self.guardar())
        self.bind("<Control-n>", lambda _e: self.nuevo())
        self.bind("<F5>", lambda _e: self.ejecutar_analisis())
        self.nuevo(ruta_inicial)

    def estilo(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background="#eef4f5")
        estilo.configure("TLabel", background="#eef4f5", foreground="#25444e", font=("Segoe UI", 10))
        estilo.configure("TButton", padding=(10, 7), font=("Segoe UI", 10))
        estilo.configure("Accent.TButton", background="#087d78", foreground="white", font=("Segoe UI", 10, "bold"))
        estilo.map("Accent.TButton", background=[("active", "#09645f")])
        estilo.configure("Treeview", rowheight=27, font=("Segoe UI", 9), background="white", fieldbackground="white")
        estilo.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), padding=7)
        estilo.configure("TNotebook.Tab", padding=(12, 8))

    def crear_interfaz(self):
        encabezado = tk.Frame(self, bg="#132f3a", padx=22, pady=15)
        encabezado.pack(fill="x")
        tk.Label(encabezado, text="HORARIOSCRIPT", font=("Segoe UI", 23, "bold"), bg="#132f3a", fg="white").pack(side="left")
        tk.Label(encabezado, text="William René Toledo Corado\n202210198 · Lenguajes Formales · B+", justify="right",
                 font=("Segoe UI", 10), bg="#132f3a", fg="#bce4dc").pack(side="right")
        barra = ttk.Frame(self, padding=(16, 12))
        barra.pack(fill="x")
        for texto, funcion in (("Nuevo", self.nuevo), ("Abrir .hor", self.abrir), ("Guardar", self.guardar), ("Guardar como…", lambda: self.guardar(True)), ("Cerrar pestaña", self.cerrar_documento)):
            ttk.Button(barra, text=texto, command=funcion).pack(side="left", padx=(0, 7))
        ttk.Button(barra, text="Analizar  F5", command=self.ejecutar_analisis, style="Accent.TButton").pack(side="right")
        self.resumen = tk.StringVar(value="Abra un archivo .hor o escriba en el editor.")
        ttk.Label(self, textvariable=self.resumen, padding=(20, 2, 20, 12), font=("Segoe UI", 11, "bold")).pack(fill="x")
        panel = ttk.Panedwindow(self, orient="horizontal")
        panel.pack(fill="both", expand=True, padx=16)
        izquierda, derecha = ttk.Frame(panel), ttk.Frame(panel)
        panel.add(izquierda, weight=5)
        panel.add(derecha, weight=6)
        ttk.Label(izquierda, text="FUENTE .HOR", font=("Segoe UI", 10, "bold"), padding=(0, 0, 0, 8)).pack(anchor="w")
        self.documentos = ttk.Notebook(izquierda)
        self.documentos.pack(fill="both", expand=True)
        self.documentos.bind("<<NotebookTabChanged>>", lambda _e: self.mostrar_resultado())
        ttk.Label(derecha, text="RESULTADOS DEL ANÁLISIS", font=("Segoe UI", 10, "bold"), padding=(10, 0, 0, 8)).pack(anchor="w")
        self.resultados = ttk.Notebook(derecha)
        self.resultados.pack(fill="both", expand=True, padx=(10, 0))
        self.tab_tokens, self.tokens = self.crear_tabla("Tokens", ("N.º", "Lexema", "Tipo", "Línea", "Columna"), (45, 180, 170, 50, 65))
        self.tab_errores, self.errores = self.crear_tabla("Errores", ("N.º", "Fase", "Lexema", "Tipo", "Descripción", "Línea", "Columna"), (40, 80, 110, 170, 310, 50, 65))
        self.tab_choques, self.choques = self.crear_tabla("Choques", ("Clases", "Día", "Traslape", "Motivos"), (80, 95, 120, 190))
        self.tab_stats, self.stats = self.crear_tabla("Estadísticas", ("Indicador", "Valor"), (270, 150))
        self.tokens.bind("<Double-1>", lambda _e: self.ir_a_token())
        self.errores.bind("<Double-1>", lambda _e: self.ir_a_error())
        self.choques.bind("<Double-1>", lambda _e: self.proponer())
        reportes = ttk.Frame(self, padding=(16, 12))
        reportes.pack(fill="x")
        ttk.Label(reportes, text="REPORTES", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))
        self.botones_resultado = []
        for etiqueta, clave in (("Horario semanal", "horario"), ("Carga docente", "carga"), ("Estadísticas", "estadisticas"), ("Diagnósticos", "errores")):
            boton = ttk.Button(reportes, text=etiqueta, command=lambda k=clave: self.abrir_reporte(k), state="disabled")
            boton.pack(side="left", padx=(0, 5))
            self.botones_resultado.append(boton)
        for etiqueta, funcion in (("Exportar tokens", self.exportar), ("Diagrama", self.diagrama)):
            boton = ttk.Button(reportes, text=etiqueta, command=funcion, state="disabled")
            boton.pack(side="left", padx=(0, 5))
            self.botones_resultado.append(boton)
        self.estado = tk.StringVar(value="Listo · Ctrl+O abrir · Ctrl+S guardar · F5 analizar")
        ttk.Label(self, textvariable=self.estado, padding=(20, 5, 20, 10), font=("Segoe UI", 9)).pack(fill="x")

    def crear_tabla(self, titulo, columnas, anchos):
        frame = ttk.Frame(self.resultados)
        self.resultados.add(frame, text=titulo)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=columnas, show="headings", selectmode="browse")
        for col, ancho in zip(columnas, anchos):
            tree.heading(col, text=col)
            tree.column(col, width=ancho, minwidth=40, stretch=col in ("Lexema", "Descripción", "Indicador"))
        sy = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        sx = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        tree.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        tree.tag_configure("error", background="#fff0ee")
        return frame, tree

    def activo(self):
        elegido = self.documentos.select()
        return self.nametowidget(elegido) if elegido else None

    def nuevo(self, ruta=None):
        try:
            contenido = leer_archivo(ruta) if ruta else ""
            doc = Documento(self.documentos, self, Path(ruta).name if ruta else "Sin título", Path(ruta) if ruta else None, contenido)
            self.documentos.add(doc, text=doc.nombre)
            self.documentos.select(doc)
            doc.texto.focus_set()
        except (OSError, ValueError, UnicodeError) as error:
            messagebox.showerror("No se pudo abrir", str(error), parent=self)

    def abrir(self):
        rutas = filedialog.askopenfilenames(parent=self, title="Abrir horarios", initialdir=BASE / "entrada", filetypes=(("HorarioScript", "*.hor"),))
        for ruta in rutas:
            self.nuevo(ruta)

    def guardar(self, como=False):
        doc = self.activo()
        if not doc:
            return False
        ruta = doc.ruta
        if ruta is None or como:
            elegida = filedialog.asksaveasfilename(parent=self, defaultextension=".hor", filetypes=(("HorarioScript", "*.hor"),), initialfile=doc.nombre if doc.ruta else "horario.hor")
            if not elegida:
                return False
            ruta = Path(elegida)
        if ruta.suffix.lower() != ".hor":
            messagebox.showerror("Extensión inválida", "Guarde el archivo con extensión .hor", parent=self)
            return False
        try:
            ruta.write_text(doc.fuente(), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("No se pudo guardar", str(error), parent=self)
            return False
        doc.ruta, doc.nombre, doc.modificado = ruta, ruta.name, False
        self.documentos.tab(doc, text=doc.nombre)
        self.estado.set(f"Guardado: {ruta}")
        return True

    def puede_cerrar(self, doc):
        if not doc.modificado:
            return True
        opcion = messagebox.askyesnocancel("Cambios sin guardar", f"¿Guardar los cambios de {doc.nombre}?", parent=self)
        if opcion is None:
            return False
        return self.guardar() if opcion else True

    def cerrar_documento(self):
        doc = self.activo()
        if doc and self.puede_cerrar(doc):
            if doc.timer is not None:
                doc.after_cancel(doc.timer)
            self.documentos.forget(doc)
            doc.destroy()
            if not self.documentos.tabs():
                self.nuevo()

    def salir(self):
        for tab in self.documentos.tabs():
            self.documentos.select(tab)
            if not self.puede_cerrar(self.nametowidget(tab)):
                return
        self.destroy()

    def ejecutar_analisis(self):
        doc = self.activo()
        if not doc:
            return
        self.configure(cursor="watch")
        self.estado.set("Analizando el editor y generando reportes…")
        self.update_idletasks()
        try:
            doc.resultado = analizar(doc.fuente())
            nombre = Path(doc.nombre).stem
            carpeta = BASE / "salidas" / (nombre + "_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
            doc.rutas = GeneradorReportes(doc.resultado, carpeta, doc.nombre).generar()
            self.mostrar_resultado()
            if doc.resultado.errores:
                self.resultados.select(self.tab_errores)
            elif doc.resultado.choques:
                self.resultados.select(self.tab_choques)
            else:
                self.resultados.select(self.tab_tokens)
            self.estado.set(f"Reportes: {carpeta} · Doble clic en un token/error para localizarlo.")
        except (OSError, ValueError) as error:
            doc.rutas = {}
            self.mostrar_resultado()
            messagebox.showerror("No se pudieron generar los reportes", str(error), parent=self)
        finally:
            self.configure(cursor="")

    def mostrar_resultado(self):
        if not hasattr(self, "tokens"):
            return
        for tabla in (self.tokens, self.errores, self.choques, self.stats):
            tabla.delete(*tabla.get_children())
        doc = self.activo()
        resultado = doc.resultado if doc else None
        for boton in self.botones_resultado:
            boton.configure(state="normal" if resultado and doc.rutas else "disabled")
        if resultado is None:
            self.resumen.set("Pendiente de análisis · F5 analiza el contenido actual del editor")
            if hasattr(self, "estado"):
                self.estado.set("Los resultados se actualizan al analizar. Cambiar el texto invalida el análisis anterior.")
            return
        for i, t in enumerate(resultado.tokens):
            self.tokens.insert("", "end", iid=str(i), values=(t.numero, t.lexema, t.tipo, t.linea, t.columna))
        for i, e in enumerate(resultado.errores):
            self.errores.insert("", "end", iid=str(i), values=(e.numero, e.fase, e.lexema, e.tipo, e.descripcion, e.linea, e.columna), tags=("error",))
        for i, c in enumerate(resultado.choques):
            self.choques.insert("", "end", iid=str(i), values=(f"#{c.primera} / #{c.segunda}", c.dia, f"{hora(c.inicio)}–{hora(c.fin)}", " y ".join(c.motivos)), tags=("error",))
        self.stats.insert("", "end", values=("Tiempo de análisis (sin reportes)", f"{resultado.milisegundos:.2f} ms"))
        for tipo, cantidad in sorted(resultado.frecuencias.items()):
            self.stats.insert("", "end", values=(tipo, cantidad))
        self.resumen.set(f"{len(resultado.tokens)} tokens  ·  {len(resultado.errores_lexicos)} errores léxicos  ·  "
                         f"{len(resultado.errores)-len(resultado.errores_lexicos)} de estructura/datos  ·  {len(resultado.choques)} choques  ·  {resultado.milisegundos:.2f} ms")

    def actualizar_cursor(self):
        doc = self.activo()
        if doc:
            linea, col = doc.texto.index("insert").split(".")
            self.estado.set(f"{doc.nombre} · Línea {linea} · Carácter {int(col)+1} · Las tablas muestran columna visual (tabulación = 4).")

    def localizar(self, inicio, fin):
        doc = self.activo()
        doc.texto.tag_remove("destino", "1.0", "end")
        doc.texto.tag_add("destino", f"1.0+{inicio}c", f"1.0+{max(inicio+1, fin)}c")
        doc.texto.see(f"1.0+{inicio}c")
        doc.texto.mark_set("insert", f"1.0+{inicio}c")
        doc.texto.focus_set()

    def ir_a_token(self):
        doc = self.activo()
        if doc.resultado and self.tokens.selection():
            t = doc.resultado.tokens[int(self.tokens.selection()[0])]
            self.localizar(t.inicio, t.fin)

    def ir_a_error(self):
        doc = self.activo()
        if doc.resultado and self.errores.selection():
            e = doc.resultado.errores[int(self.errores.selection()[0])]
            self.localizar(e.inicio, e.fin)

    def proponer(self):
        doc = self.activo()
        if doc.resultado and self.choques.selection():
            choque = doc.resultado.choques[int(self.choques.selection()[0])]
            clase = next(c for c in doc.resultado.horario.clases if c.numero == choque.segunda)
            opciones = sugerir_libres(doc.resultado.horario, clase)
            texto = "\n".join(f"{d}: {hora(i)}–{hora(f)}" for d, i, f in opciones) or "No hay bloques libres para esta duración."
            messagebox.showinfo(f"Opciones para la clase #{clase.numero}", texto + "\n\nPropuestas orientativas; modifique la entrada para aplicarlas.", parent=self)

    def abrir_reporte(self, clave):
        doc = self.activo()
        if doc and clave in doc.rutas:
            try:
                webbrowser.open(doc.rutas[clave].resolve().as_uri())
            except OSError as error:
                messagebox.showerror("No se pudo abrir el navegador", str(error), parent=self)

    def exportar(self):
        doc = self.activo()
        if not doc or not doc.resultado:
            return
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension=".json", initialfile="tokens.json", filetypes=(("JSON", "*.json"), ("CSV", "*.csv")))
        if ruta:
            try:
                exportar_tokens(doc.resultado.tokens, ruta)
                self.estado.set(f"Tokens exportados: {ruta}")
            except (OSError, ValueError) as error:
                messagebox.showerror("No se pudo exportar", str(error), parent=self)

    def diagrama(self):
        doc = self.activo()
        if doc and "dot" in doc.rutas:
            try:
                svg = renderizar_dot(doc.rutas["dot"])
                webbrowser.open(svg.resolve().as_uri())
            except (OSError, ValueError) as error:
                messagebox.showinfo("Diagrama DOT disponible", f"{error}\n\nArchivo: {doc.rutas['dot']}", parent=self)
            except Exception as error:
                messagebox.showerror("Graphviz no pudo renderizar", str(error), parent=self)
