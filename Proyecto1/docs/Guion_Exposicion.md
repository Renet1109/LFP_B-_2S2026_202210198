# Guion de exposición · 8 a 10 minutos

William René Toledo Corado · 202210198 · Lenguajes Formales B+

## 1. Presentación (1 minuto)

Explicar el problema: verificar horarios estructurados, identificar lexemas inválidos y evitar asignar el mismo docente o aula a clases simultáneas. Mostrar las cuatro secciones del lenguaje. Indicar que el lexer es un AFD manual escrito en Python, sin `re` ni generadores.

## 2. Archivo válido (2 minutos)

Ejecutar `python main.py entrada/01_valido.hor`, pulsar F5 y mostrar las columnas número, lexema, tipo, línea y columna. Mostrar `BD2-0812` y explicar la decisión tomada a partir del ejemplo del enunciado. Abrir los tres reportes.

## 3. Recuperación y choques (2 minutos)

Abrir `02_caracteres.hor` y analizar: hay tres errores léxicos en la línea 3, columnas 1, 3 y 5, pero se siguen leyendo las dos clases. Doble clic en un error para localizarlo. Después abrir `demo.hor`: siete clases y un choque de docente entre las clases 5 y 6 el lunes de 07:30 a 08:40. Mostrar rojo en el horario y las propuestas al hacer doble clic en el choque. Aclarar que ninguna propuesta modifica la entrada automáticamente.

## 4. Explicación técnica (2 minutos)

Mostrar `docs/diagramas/afd.svg` y el método `siguiente_token()` en `horarioscript/lexer.py`. Recorrer 07:00: I consume 0, NUM consume 7, ':' cambia a HORA, se consumen 00 y el delimitador provoca la validación y emisión sin perder el delimitador. Recorrer un comentario y una cadena sin cerrar.

Mostrar la clase Token original ampliada con valor y offsets; explicar cómo GestorErrores acumula los errores. La forma léxica y la consistencia estructural se validan en fases distintas.

## 5. Pruebas y decisiones (1 minuto)

Ejecutar `python -m unittest discover -s tests -v`. Explicar una prueba independiente de choques: comparar el algoritmo con la intersección de conjuntos de minutos. Mostrar la evidencia de los doce casos. Mencionar que las cuatro semanas propuestas por el documento no se han recreado artificialmente en Git.

## Preguntas para practicar

1. **¿Por qué es determinista?** En cada estado las clases de entrada son disjuntas y hay una sola transición; las salidas dependen de validadores definidos, sin retroceso para elegir alternativas.
2. **¿Cómo se resuelve palabra reservada frente a código?** Se consume la secuencia completa y se busca igualdad exacta en las tablas; si no coincide, se valida el código mediante su sub-AFD.
3. **¿Por qué se conserva el delimitador?** Pertenece al siguiente token. Al aceptar un candidato no se avanza sobre ese carácter.
4. **¿Qué ocurre con una hora fuera de rango?** Su forma se reconoce como candidato; el validador exige cinco caracteres, ':' en la posición 3, dígitos y minutos en el rango institucional.
5. **¿Cuándo chocan dos clases?** Mismo día, docente o aula compartido, y `max(inicios) < min(finales)`. La igualdad implica adyacencia, no choque.
6. **¿Por qué hay errores sintácticos?** Son diagnósticos auxiliares del lector que construye reportes; no se mezclan con los errores del AFD ni reemplazan el objetivo léxico del proyecto.
7. **¿Por qué la carga y la ocupación se calculan diferente?** La carga suma asignaciones; un aula solo puede estar ocupada una vez en un mismo minuto, por eso se une el intervalo.
8. **¿Un comentario puede quedar sin cerrar?** No con `##`; el propio EOF lo cierra. Sí puede quedar sin cerrar una cadena, y hay una prueba separada.
9. **¿Se permiten dos clases de la misma sección simultáneas?** El criterio obligatorio de choque solo usa docente o aula; la propuesta opcional de reprogramación evita además ocupar la sección.
10. **¿Qué aporta el primer commit?** Las clases Token y GestorErrores; sus métodos se conservan y se amplían. El código se completó con asistencia de IA: estudiar la implementación y explicar las decisiones con palabras propias.
