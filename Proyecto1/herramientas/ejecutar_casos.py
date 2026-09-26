"""Ejecuta las expectativas publicadas y registra la evidencia sin inventar resultados."""
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))
from horarioscript.servicio import analizar, leer_archivo


def main():
    evidencia = []
    for caso in json.loads((BASE / 'entrada/casos.json').read_text(encoding='utf-8')):
        r = analizar(leer_archivo(BASE / 'entrada' / caso['archivo']))
        obtenido = {'tipos_lexicos': [e.tipo for e in r.errores_lexicos], 'choques': len(r.choques), 'clases_validas': len(r.horario.clases)}
        evidencia.append({**caso, 'obtenido': obtenido, 'aprobado': obtenido == caso['esperado'],
                          'tokens': len(r.tokens), 'milisegundos': r.milisegundos,
                          'diagnosticos': [vars(e) for e in r.errores]})
    destino = BASE / 'docs/evidencia_casos.json'
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), encoding='utf-8')
    for caso in evidencia:
        print(('PASS' if caso['aprobado'] else 'FAIL') + ' ' + caso['archivo'])
    return 0 if all(c['aprobado'] for c in evidencia) else 1


if __name__ == '__main__':
    raise SystemExit(main())
