"""Exporta DDL 009 para Data Modeler: solo metadatos, sin filas ni credenciales."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import re
import tomllib

ROOT=Path(__file__).resolve().parents[1]


def exportar(configuracion, destino):
    import oracledb
    config=tomllib.loads(Path(configuracion).read_text(encoding='utf-8'))
    partes=['-- UPC Aula: modelo relacional 009 para inspeccion / importacion en Data Modeler.',
        '-- Exportacion de metadatos: no incluye filas de personas, claves ni conexion.',
        '-- Para instalar la aplicacion utilice oracle_scripts.sql en un esquema nuevo.',
        '-- No ejecutar este DDL sobre la base existente para generar un diagrama.',
        'SET DEFINE OFF', '']
    with oracledb.connect(user=config['ORACLE_USUARIO'],password=config['ORACLE_CONTRASENA'],
                          dsn=config['ORACLE_DSN'],tcp_connect_timeout=10,retry_count=0) as conn:
        conn.call_timeout=15000
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute("SELECT USER,SYS_CONTEXT('USERENV','CURRENT_SCHEMA') FROM dual")
            usuario,esquema=cur.fetchone()
            if usuario!=esquema or usuario in ('SYS','SYSTEM','ADMIN'):
                raise ValueError('Conecta como propietario del proyecto para leer sus metadatos.')
            cur.execute('SELECT version FROM versiones_esquema ORDER BY version')
            if [r[0] for r in cur.fetchall()]!=[f'{n:03d}' for n in range(1,10)]:
                raise ValueError('El modelo de esta entrega requiere el esquema 001–009.')
            cur.execute('''BEGIN
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'SQLTERMINATOR',TRUE);
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'SEGMENT_ATTRIBUTES',FALSE);
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'EMIT_SCHEMA',FALSE);
                DBMS_METADATA.SET_TRANSFORM_PARAM(DBMS_METADATA.SESSION_TRANSFORM,'REF_CONSTRAINTS',FALSE);
                END;''')
            consultas=[('TABLE','SELECT table_name FROM user_tables ORDER BY table_name'),
                ('REF_CONSTRAINT',"SELECT constraint_name FROM user_constraints WHERE constraint_type='R' ORDER BY table_name,constraint_name"),
                ('INDEX',"SELECT index_name FROM user_indexes WHERE generated='N' AND index_name NOT IN (SELECT index_name FROM user_constraints WHERE index_name IS NOT NULL) ORDER BY index_name"),
                ('VIEW','SELECT view_name FROM user_views ORDER BY view_name')]
            conteos={}
            for tipo,sql in consultas:
                cur.execute(sql);nombres=[r[0] for r in cur.fetchall()];conteos[tipo]=len(nombres)
                partes.append('-- '+tipo)
                for nombre in nombres:
                    if not re.fullmatch(r'[A-Z][A-Z0-9_$#]*',nombre):raise ValueError('Nombre de objeto no admitido.')
                    cur.execute('SELECT DBMS_METADATA.GET_DDL(:t,:n) FROM dual',t=tipo,n=nombre)
                    valor=cur.fetchone()[0]
                    partes.append(valor.read() if hasattr(valor,'read') else str(valor))
        conn.rollback()
    if conteos['TABLE']!=14 or conteos['REF_CONSTRAINT']!=11:raise ValueError('El inventario no coincide con 009.')
    destino=Path(destino);destino.parent.mkdir(parents=True,exist_ok=True)
    destino.write_text('\n\n'.join(partes)+'\n',encoding='utf-8')
    estado=dict(estado='exportado',esquema='009',solo_metadatos=True,conteos=conteos,
        fecha_utc=datetime.now(timezone.utc).isoformat())
    privado=ROOT/'.local/paquete_presentacion';privado.mkdir(parents=True,exist_ok=True)
    (privado/'exportacion_modelo.json').write_text(json.dumps(estado,indent=2),encoding='utf-8')
    print(json.dumps(estado))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--configuracion',type=Path,default=ROOT/'.local/oracle_cloud/credenciales_tecnicas.toml')
    p.add_argument('--salida',type=Path,default=ROOT/'exports/modelo_009.sql')
    args=p.parse_args();exportar(args.configuracion,args.salida)


if __name__=='__main__':main()
