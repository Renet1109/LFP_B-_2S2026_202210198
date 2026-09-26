# Casos ejecutados

**William René Toledo Corado · 202210198 · B+**

12 casos y 44 pruebas automatizadas. Evidencia: evidencia_casos.json.

## Entrada base

```text
## Horario Lenguajes Formales - Segundo Semestre 2026
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
```

## 01. Ejemplo del enunciado

Archivo: `01_valido.hor`.

Entrada: Sin cambios: entrada base completa de la página anterior.

Esperado: Errores léxicos: ninguno. Choques: 0. Clases válidas: 2.

Obtenido: PASS. 149 tokens válidos; 0 errores léxicos; 0 choques; 2 clases válidas.

Diagnósticos: ninguno.

## 02. Recuperación ante @, % y ~

Archivo: `02_caracteres.hor`.

Entrada: Se inserta una línea con @ % ~ antes de CURSOS. Se esperan errores en línea 3, columnas 1, 3 y 5.

Esperado: Errores léxicos: CARACTER_NO_RECONOCIDO, CARACTER_NO_RECONOCIDO, CARACTER_NO_RECONOCIDO. Choques: 0. Clases válidas: 2.

Obtenido: PASS. 149 tokens válidos; 3 errores léxicos; 0 choques; 2 clases válidas.

Diagnósticos: CARACTER_NO_RECONOCIDO (3:1, LEXICO); CARACTER_NO_RECONOCIDO (3:3, LEXICO); CARACTER_NO_RECONOCIDO (3:5, LEXICO).

## 03. Hora anterior a 06:00

Archivo: `03_hora_rango.hor`.

Entrada: En la primera clase se sustituye inicio: 07:00 por inicio: 05:59.

Esperado: Errores léxicos: HORA_FUERA_DE_RANGO. Choques: 0. Clases válidas: 1.

Obtenido: PASS. 148 tokens válidos; 1 errores léxicos; 0 choques; 1 clases válidas.

Diagnósticos: HORA_FUERA_DE_RANGO (16:65, LEXICO).

## 04. DOMINGO no pertenece al lenguaje

Archivo: `04_dia.hor`.

Entrada: En la primera clase se sustituye dia: LUNES por dia: DOMINGO.

Esperado: Errores léxicos: DIA_NO_RECONOCIDO. Choques: 0. Clases válidas: 1.

Obtenido: PASS. 148 tokens válidos; 1 errores léxicos; 0 choques; 1 clases válidas.

Diagnósticos: DIA_NO_RECONOCIDO (16:50, LEXICO).

## 05. Código sin guion

Archivo: `05_codigo.hor`.

Entrada: En el primer curso se sustituye codigo: "LFP-0796" por codigo: "LFP0796". La clase que lo referencia no puede usarse.

Esperado: Errores léxicos: CODIGO_MAL_FORMADO. Choques: 0. Clases válidas: 1.

Obtenido: PASS. 148 tokens válidos; 1 errores léxicos; 0 choques; 1 clases válidas.

Diagnósticos: CODIGO_MAL_FORMADO (4:56, LEXICO); REFERENCIA_INEXISTENTE (16:1, SEMANTICO).

## 06. Comentario sin salto final: EOF lo cierra

Archivo: `06_comentario_eof.hor`.

Entrada: Al final se agrega, sin salto posterior: ## comentario sin cerrar aparente: @ % ~ "

Esperado: Errores léxicos: ninguno. Choques: 0. Clases válidas: 2.

Obtenido: PASS. 150 tokens válidos; 0 errores léxicos; 0 choques; 2 clases válidas.

Diagnósticos: ninguno.

## 07. Cadena sin comilla de cierre

Archivo: `07_cadena.hor`.

Entrada: La primera declaración de curso se reemplaza por: curso: "Cadena sin cerrar. La línea siguiente sigue procesándose.

Esperado: Errores léxicos: CADENA_SIN_CERRAR. Choques: 0. Clases válidas: 1.

Obtenido: PASS. 138 tokens válidos; 1 errores léxicos; 0 choques; 1 clases válidas.

Diagnósticos: CADENA_SIN_CERRAR (4:8, LEXICO); REFERENCIA_INEXISTENTE (16:1, SEMANTICO).

## 08. Docente simultáneo en dos aulas y secciones

Archivo: `08_choque_docente.hor`.

Entrada: Se agrega al inicio de CLASES: clase: "BD2-0812" con "DOC-001" en "LAB-3" [dia: LUNES, inicio: 07:30, fin: 09:00, seccion: "B+"],

Esperado: Errores léxicos: ninguno. Choques: 1. Clases válidas: 3.

Obtenido: PASS. 174 tokens válidos; 0 errores léxicos; 1 choques; 3 clases válidas.

Diagnósticos: ninguno.

## 09. Aula simultánea con dos docentes

Archivo: `09_choque_aula.hor`.

Entrada: Se agrega al inicio de CLASES: clase: "BD2-0812" con "DOC-002" en "A-101" [dia: LUNES, inicio: 08:00, fin: 09:00, seccion: "B+"],

Esperado: Errores léxicos: ninguno. Choques: 1. Clases válidas: 3.

Obtenido: PASS. 174 tokens válidos; 0 errores léxicos; 1 choques; 3 clases válidas.

Diagnósticos: ninguno.

## 10. 06:00, 21:00 e intervalos adyacentes

Archivo: `10_limites.hor`.

Entrada: Primera clase: LUNES 06:00-07:00. Segunda clase: LUNES 07:00-21:00 en A-101. Comparten aula y son adyacentes, sin traslape.

Esperado: Errores léxicos: ninguno. Choques: 0. Clases válidas: 2.

Obtenido: PASS. 149 tokens válidos; 0 errores léxicos; 0 choques; 2 clases válidas.

Diagnósticos: ninguno.

## 11. Catálogos vacíos, sin división por cero

Archivo: `11_vacio.hor`.

Entrada: HORARIO { CURSOS {}; CATEDRATICOS {}; AULAS {}; CLASES {}; };

Esperado: Errores léxicos: ninguno. Choques: 0. Clases válidas: 0.

Obtenido: PASS. 20 tokens válidos; 0 errores léxicos; 0 choques; 0 clases válidas.

Diagnósticos: ninguno.

## 12. Hora de un dígito: 7:00

Archivo: `12_formato_hora.hor`.

Entrada: En la primera clase se sustituye inicio: 07:00 por inicio: 7:00.

Esperado: Errores léxicos: HORA_FUERA_DE_RANGO. Choques: 0. Clases válidas: 1.

Obtenido: PASS. 148 tokens válidos; 1 errores léxicos; 0 choques; 1 clases válidas.

Diagnósticos: HORA_FUERA_DE_RANGO (16:65, LEXICO).