"""Exporta solo metadatos Oracle a un catálogo HTML y un diccionario; no lee filas de negocio."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tomllib

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def leer_catalogo(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT version FROM versiones_esquema ORDER BY version')
        versiones = [f[0] for f in cur.fetchall()]
        cur.execute('''SELECT t.table_name,c.comments FROM user_tables t
            LEFT JOIN user_tab_comments c ON c.table_name=t.table_name ORDER BY t.table_name''')
        tablas = {n: dict(nombre=n, comentario=c or '', columnas=[], restricciones=[]) for n, c in cur.fetchall()}
        cur.execute('''SELECT c.table_name,c.column_name,c.data_type,c.data_length,c.char_length,
            c.char_used,c.data_precision,c.data_scale,c.nullable,c.identity_column,co.comments
            FROM user_tab_columns c LEFT JOIN user_col_comments co
              ON co.table_name=c.table_name AND co.column_name=c.column_name
            ORDER BY c.table_name,c.column_id''')
        for tabla, nombre, tipo, longitud, caracteres, semantica, precision, escala, nulo, identidad, comentario in cur:
            if tabla not in tablas:
                continue
            if tipo in ('VARCHAR2', 'NVARCHAR2', 'CHAR', 'NCHAR'):
                tipo += f'({caracteres if semantica == "C" else longitud} {"CHAR" if semantica == "C" else "BYTE"})'
            elif tipo == 'NUMBER' and precision is not None:
                tipo += f'({precision},{escala})'
            tablas[tabla]['columnas'].append(dict(nombre=nombre, tipo=tipo, admite_nulo=nulo == 'Y',
                identidad=identidad == 'YES', comentario=comentario or '', predeterminado=''))
        columnas = {(t['nombre'], c['nombre']): c for t in tablas.values() for c in t['columnas']}
        cur.execute('SELECT table_name,column_name,data_default FROM user_tab_columns')
        for tabla, nombre, predeterminado in cur:
            if (tabla, nombre) in columnas:
                c = columnas[(tabla, nombre)]
                c['predeterminado'] = 'Identidad Oracle' if c['identidad'] else (predeterminado or '').strip()
        cur.execute('''SELECT c.table_name,c.constraint_name,c.constraint_type,cc.column_name,cc.position,
            r.table_name,rc.column_name,c.delete_rule,c.status,c.validated
            FROM user_constraints c LEFT JOIN user_cons_columns cc ON cc.constraint_name=c.constraint_name
            LEFT JOIN user_constraints r ON r.constraint_name=c.r_constraint_name
            LEFT JOIN user_cons_columns rc ON rc.constraint_name=r.constraint_name AND rc.position=cc.position
            ORDER BY c.table_name,c.constraint_name,cc.position''')
        restricciones = {}
        for tabla, nombre, tipo, columna, posicion, referencia, ref_columna, borrar, estado, validacion in cur:
            if tabla not in tablas:
                continue
            clave = (tabla, nombre)
            if clave not in restricciones:
                restricciones[clave] = dict(nombre=nombre, tipo=tipo, columnas=[], referencia=referencia,
                    columnas_referencia=[], al_eliminar=borrar, estado=estado, validacion=validacion, condicion='')
                tablas[tabla]['restricciones'].append(restricciones[clave])
            if columna:
                restricciones[clave]['columnas'].append(columna)
            if ref_columna:
                restricciones[clave]['columnas_referencia'].append(ref_columna)
        # SEARCH_CONDITION es LONG; leerlo separado evita restricciones del driver/joins.
        cur.execute("SELECT table_name,constraint_name,search_condition FROM user_constraints WHERE constraint_type='C'")
        for tabla, nombre, condicion in cur:
            if (tabla, nombre) in restricciones:
                restricciones[(tabla, nombre)]['condicion'] = condicion or ''
    return dict(generado_utc=datetime.now(timezone.utc).isoformat(), versiones=versiones,
        alcance='Metadatos del esquema propietario; sin filas, usuarios Oracle, DSN ni credenciales.', tablas=list(tablas.values()))


def _md(valor):
    return str(valor).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def diccionario(catalogo):
    lineas = ['# Diccionario de datos vigente', '',
        'Generado desde el diccionario Oracle; no contiene registros de personas ni credenciales.', '',
        f"Versiones: {', '.join(catalogo['versiones'])}. Captura UTC: {catalogo['generado_utc']}.", '',
        '[Visualización interactiva](base_datos/index.html) · [Explicación funcional](BASE_DE_DATOS.md) · '
        '[Conexión](CONEXION_BASE_DATOS.md)', '',
        'PK = clave primaria; FK = clave foránea; UQ = unicidad. Las condiciones CHECK '
        'incluyen las reglas NOT NULL de Oracle. La identidad indica numeración global automática.', '']
    for t in catalogo['tablas']:
        lineas += [f"## {t['nombre']}", '', _md(t['comentario']), '',
            '| Columna | Tipo | Admite NULL | Identidad | Claves | Predeterminado | Descripción |',
            '| --- | --- | --- | --- | --- | --- | --- |']
        for c in t['columnas']:
            claves = ', '.join({'P':'PK','R':'FK','U':'UQ'}.get(r['tipo'], '') for r in t['restricciones']
                if c['nombre'] in r['columnas'] and r['tipo'] in ('P','R','U'))
            lineas.append('| ' + ' | '.join(_md(v) for v in (c['nombre'], c['tipo'],
                'Sí' if c['admite_nulo'] else 'No', 'Sí' if c['identidad'] else 'No', claves,
                c['predeterminado'], c['comentario'])) + ' |')
        lineas += ['', '| Restricción | Regla | Estado |', '| --- | --- | --- |']
        for r in t['restricciones']:
            regla = {'P':'PK', 'U':'UNIQUE', 'R':'FK', 'C':'CHECK'}.get(r['tipo'], r['tipo']) + ' (' + ', '.join(r['columnas']) + ')'
            if r['referencia']:
                regla += ' → ' + r['referencia'] + '(' + ', '.join(r['columnas_referencia']) + ') · ON DELETE ' + r['al_eliminar']
            if r['condicion']:
                regla += ': ' + r['condicion']
            lineas.append('| ' + ' | '.join(_md(v) for v in (r['nombre'], regla, r['estado']+' / '+r['validacion'])) + ' |')
        lineas.append('')
    return '\n'.join(lineas).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuracion', type=Path, required=True, help='TOML privado de la cuenta propietaria.')
    args = parser.parse_args()
    import oracledb
    config = tomllib.loads(args.configuracion.read_text(encoding='utf-8'))
    with oracledb.connect(user=config['ORACLE_USUARIO'], password=config['ORACLE_CONTRASENA'],
                          dsn=config['ORACLE_DSN'], tcp_connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute("SELECT SYS_CONTEXT('USERENV','SESSION_USER'),SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM dual")
            usuario, esquema = cur.fetchone()
            if usuario != esquema or usuario in ('SYS','SYSTEM','ADMIN'):
                raise ValueError('Conecta con el propietario del esquema del proyecto.')
        catalogo = leer_catalogo(conn)
    significados = json.loads((RAIZ/'scripts/plantillas/significados_bd.json').read_text(encoding='utf-8'))
    for tabla in catalogo['tablas']:
        notas = significados.get(tabla['nombre'], {})
        if not tabla['comentario']:
            tabla['comentario'] = notas.get('_tabla', '')
        for columna in tabla['columnas']:
            if not columna['comentario']:
                columna['comentario'] = notas.get(columna['nombre'], '')
    destino = RAIZ / 'docs/base_datos'
    destino.mkdir(exist_ok=True)
    contenido = json.dumps(catalogo, ensure_ascii=False, indent=2)
    (destino / 'catalogo.json').write_text(contenido+'\n', encoding='utf-8')
    plantilla = (RAIZ / 'scripts/plantillas/catalogo_bd.html').read_text(encoding='utf-8')
    (destino / 'index.html').write_text(plantilla.replace('__CATALOGO_JSON__', contenido.replace('<', '\\u003c')), encoding='utf-8')
    (RAIZ / 'docs/DICCIONARIO_DATOS.md').write_text(diccionario(catalogo), encoding='utf-8')
    print(f"Catálogo generado: {len(catalogo['tablas'])} tablas; versión {catalogo['versiones'][-1]}; solo metadatos.")


if __name__ == '__main__':
    main()
