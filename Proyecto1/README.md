# HorarioScript · Proyecto 1

**William René Toledo Corado · 202210198 · LFP B+ · Segundo semestre 2026**

Analizador léxico manual de horarios académicos con Python 3.10+ y Tkinter. Lee `.hor`, muestra tokens y errores con línea/columna, detecta choques de docente o aula y genera reportes HTML independientes con CSS embebido.

## Ejecutar

Instala Python 3.10 o superior desde [python.org](https://www.python.org/downloads/), incluyendo Tcl/Tk. En Windows activa la opción de agregar Python a PATH. Abre una terminal en esta carpeta:

```powershell
python --version
python -m tkinter
python main.py
```

También puedes abrir `ejecutar.bat` en Windows o `INICIAR_HORARIOSCRIPT.bat` en la raíz del repositorio. El iniciador busca `py -3`, `python` y, como alternativa local, el runtime de Python de Codex si ya está instalado en el perfil del usuario. No descarga ni instala software. Si tu instalación usa el lanzador `py`, reemplaza `python` por `py -3`.

**La aplicación no requiere `pip install`.** Graphviz solo se necesita para convertir DOT a SVG; el análisis, la GUI, los reportes HTML y la generación de DOT funcionan sin él. Los diagramas SVG/PNG del diseño ya están incluidos en `docs/diagramas`.

```powershell
python main.py entrada/demo.hor
python main.py --analizar entrada/01_valido.hor --salida salidas/valido
python main.py --analizar entrada/08_choque_docente.hor --salida salidas/choque
```

El código de salida de consola es **0** si no hay errores ni choques, **1** si existen diagnósticos o choques y **2** si falla la lectura o la generación. Que un caso de prueba inválido devuelva 1 es el resultado esperado.

## Uso rápido

1. Pulsa **Abrir .hor** y selecciona uno o varios archivos de `entrada`.
2. Pulsa **Analizar / F5**. Se analiza lo que está en el editor, incluidos cambios sin guardar.
3. Revisa **Tokens**, **Errores**, **Choques** y **Estadísticas**. Doble clic en un token o error localiza su texto; doble clic en un choque propone horarios libres.
4. Abre **Horario semanal**, **Carga docente**, **Estadísticas** o **Diagnósticos**. Los archivos se guardan en una carpeta única dentro de `salidas`.
5. **Exportar tokens** guarda CSV o JSON. **Diagrama** convierte el DOT a SVG si `dot` está disponible en PATH.

Cambiar el editor invalida sus resultados anteriores. Cada pestaña mantiene su propio análisis; antes de cerrar se pregunta por cambios sin guardar. El resaltado es en vivo para entradas de hasta 200 000 caracteres; el análisis completo no depende de ese límite.

## Pruebas

```powershell
python -m unittest discover -s tests -v
python herramientas/ejecutar_casos.py
```

Se incluyen 44 pruebas automatizadas y 12 casos documentados, con expectativas en `entrada/casos.json` y evidencia en `docs/evidencia_casos.json`. Las pruebas abarcan los 1440 minutos del día y combinaciones de intervalos comparadas contra conjuntos de minutos.

## Estructura

```text
Proyecto1/
  main.py                       GUI o consola
  analizador_lexico.py           Importación compatible de AnalizadorLexico
  gestor_errores.py              Importaciones compatibles de las clases base
  horarioscript/
    token.py                    Clase Token original ampliada
    gestor_errores.py            Clases originales ampliadas
    lexer.py                    AFD manual, siguiente_token()
    lector.py                   Extracción y validación estructural
    modelos.py                  Curso, Catedratico, Aula, Clase, Horario, Resultado
    servicio.py                 Análisis, choques, cargas y ocupación
    reportes.py                 HTML, DOT, CSV y JSON
    gui.py                      Tkinter y documentos por pestaña
  entrada/                      12 pruebas y demo.hor
  tests/                        unittest
  herramientas/                 Generación de casos, diagramas y documentación
  docs/                         Manuales PDF/MD y evidencia real
  salidas/                      Resultados de ejecución, excluidos de Git
```

## Decisiones del lenguaje

- Se acepta `BD2-0812` porque figura en el ejemplo oficial: prefijo iniciado en letra ASCII, seguido de letras/dígitos, guion y uno o más dígitos. Se reconocen códigos con o sin comillas conforme a la tabla y las reglas de prioridad.
- `##` termina en salto de línea o EOF; no existe comentario de línea sin cerrar. El caso 06 documenta esa contradicción y el caso 07 prueba una cadena sin cerrar.
- Horas exactamente `HH:MM`, de 06:00 a 21:00 inclusive. Un bloque necesita `fin > inicio`.
- Mayúsculas/minúsculas son significativas. Las cadenas admiten Unicode y escapes. CRLF cuenta como un salto; tabulación avanza a la próxima columna múltiplo de cuatro contando desde 1.
- Cada sección obligatoria aparece una vez. Se permiten catálogos vacíos y sección de clase opcional. Créditos/capacidad deben ser positivos y las referencias deben existir.
- Los errores de estructura y datos se muestran separados de los errores léxicos. Los reportes con diagnósticos se identifican como parciales.
- Los intervalos son semiabiertos: terminar a las 08:00 y comenzar a las 08:00 no es un choque. Un par que comparte docente y aula cuenta una sola vez, con ambos motivos.
- Carga: suma de duraciones. Ocupación: unión de intervalos sobre 90 horas semanales por aula. Los umbrales continuos y sus razones están en el manual técnico.

## Documentación

- [Manual técnico](docs/Manual_Tecnico.pdf) / [fuente Markdown](docs/Manual_Tecnico.md)
- [Manual de usuario](docs/Manual_Usuario.pdf) / [fuente Markdown](docs/Manual_Usuario.md)
- [Casos de prueba](docs/Casos_de_Prueba.pdf) / [fuente Markdown](docs/Casos_de_Prueba.md)
- [Guion de exposición y preguntas](docs/Guion_Exposicion.md)
- [Reportes de demostración](docs/reportes_demo/horario.html)

Para regenerar las imágenes de los diagramas, instala [Graphviz](https://graphviz.org/download/) y ejecuta `python herramientas/diagramas.py dot`. Para reconstruir los manuales se necesita `reportlab`, indicado en `requirements-docs.txt`; esta dependencia no se usa en el programa.

## Continuidad del avance

Se conserva el commit inicial `86118a7` del estudiante. Se ampliaron sus clases Token, ErrorLexico y GestorErrores y se mantuvieron los métodos originales. `token.py` se movió al paquete `horarioscript` para evitar ocultar el módulo homónimo de Python. Se añadió la carpeta `Proyecto1` dentro del repositorio conforme al enunciado.

El repositorio conserva el nombre `LFP_B-_2S2026_202210198` por solicitud del estudiante; su sección real es **B+**. Desarrollo completado con asistencia de IA y commits con fechas reales. No se simula un historial de cuatro semanas ni se requieren cuatro releases para este proyecto.
