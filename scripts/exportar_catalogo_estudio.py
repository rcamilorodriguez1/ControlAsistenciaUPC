"""Captura metadatos 011 para la guía didáctica; no consulta filas de personas."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import tomllib

from _comun import RAIZ,usar_entorno
from generar_catalogo_bd import leer_catalogo


def capturar(configuracion,salida):
    import oracledb
    config=tomllib.loads(Path(configuracion).read_text(encoding='utf-8'))
    with oracledb.connect(user=config['ORACLE_USUARIO'],password=config['ORACLE_CONTRASENA'],
                         dsn=config['ORACLE_DSN'],tcp_connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute("SELECT USER,SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM dual")
            if cur.fetchone()!=('UPC_ASISTENCIA','UPC_ASISTENCIA'):
                raise ValueError('Se requiere el propietario del proyecto.')
        catalogo=leer_catalogo(conn)
        if catalogo['versiones'][-1]!='011':raise ValueError('La guía corresponde al esquema 011.')
        with conn.cursor() as cur:
            cur.execute('SELECT view_name,text FROM user_views ORDER BY view_name')
            catalogo['vistas']=[{'nombre':n,'sql':t} for n,t in cur]
            cur.execute("SELECT name,line,text FROM user_source WHERE type='PACKAGE' ORDER BY name,line")
            paquetes={}
            for n,linea,texto in cur:
                paquetes.setdefault(n,{'nombre':n,'especificacion':'','rutinas':[]})['especificacion']+=texto
            cur.execute('''SELECT object_name,procedure_name FROM user_procedures
                WHERE object_type='PACKAGE' AND procedure_name IS NOT NULL ORDER BY object_name,subprogram_id''')
            for n,p in cur:paquetes[n]['rutinas'].append({'nombre':p,'argumentos':[]})
            cur.execute('''SELECT package_name,object_name,argument_name,position,data_type,in_out,defaulted
                FROM user_arguments WHERE package_name IS NOT NULL AND data_level=0
                ORDER BY package_name,object_name,sequence''')
            for paquete,rutina,nombre,posicion,tipo,direccion,defecto in cur:
                if paquete not in paquetes:continue
                for r in paquetes[paquete]['rutinas']:
                    if r['nombre']==rutina:
                        r['argumentos'].append({'nombre':nombre,'posicion':posicion,'tipo':tipo,
                            'direccion':direccion,'predeterminado':defecto=='Y'})
            catalogo['paquetes']=list(paquetes.values())
            cur.execute('''SELECT trigger_name,table_name,trigger_type,triggering_event,status,trigger_body
                FROM user_triggers ORDER BY trigger_name''')
            catalogo['disparadores']=[dict(zip(['nombre','tabla','momento','evento','estado','cuerpo'],r)) for r in cur]
            cur.execute('SELECT index_name,table_name,uniqueness,index_type,status FROM user_indexes ORDER BY table_name,index_name')
            catalogo['indices']=[dict(zip(['nombre','tabla','unicidad','tipo','estado'],r)) for r in cur]
            cur.execute('SELECT index_name,column_position,column_expression FROM user_ind_expressions ORDER BY index_name,column_position')
            catalogo['expresiones_indices']=[dict(zip(['indice','posicion','expresion'],r)) for r in cur]
            cur.execute('SELECT table_name,column_name,generation_type FROM user_tab_identity_cols ORDER BY table_name')
            catalogo['identidades']=[dict(zip(['tabla','columna','generacion'],r)) for r in cur]
    significados=json.loads((RAIZ/'scripts/plantillas/significados_bd.json').read_text(encoding='utf-8'))
    for t in catalogo['tablas']:
        if not t['comentario']:t['comentario']=significados.get(t['nombre'],{}).get('_tabla','')
        for c in t['columnas']:
            if not c['comentario']:c['comentario']=significados.get(t['nombre'],{}).get(c['nombre'],'')
    catalogo['fecha_guia']=datetime.now(timezone.utc).isoformat()
    salida=Path(salida);salida.parent.mkdir(parents=True,exist_ok=True)
    salida.write_text(json.dumps(catalogo,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'salida':str(salida),'tablas':len(catalogo['tablas']),
        'columnas':sum(len(t['columnas']) for t in catalogo['tablas']),
        'fk':sum(r['tipo']=='R' for t in catalogo['tablas'] for r in t['restricciones']),
        'vistas':len(catalogo['vistas']),'paquetes':len(catalogo['paquetes']),
        'rutinas':sum(len(p['rutinas']) for p in catalogo['paquetes']),
        'triggers':len(catalogo['disparadores']),'indices':len(catalogo['indices']),
        'identidades':len(catalogo['identidades']),'filas_personales_consultadas':0},ensure_ascii=False))


def main():
    usar_entorno()
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configuracion',type=Path,required=True)
    p.add_argument('--salida',type=Path,default=RAIZ/'docs/base_datos/catalogo_estudio_011.json')
    a=p.parse_args();capturar(a.configuracion,a.salida)


if __name__=='__main__':main()
