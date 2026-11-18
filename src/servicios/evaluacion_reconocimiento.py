"""Evaluación reproducible sobre referencias y consultas etiquetadas, sin capturas reales implícitas."""

from src.servicios.identificacion import ClasificadorReferencias


def evaluar(datos, *, umbral=None, margen=None):
    if datos.get('origen') not in ('sintetico', 'consentido') or (datos.get('origen') == 'consentido' and datos.get('consentimiento') is not True):
        raise ValueError('Indica datos sintéticos o un conjunto consentido explícitamente.')
    referencias = datos['referencias']
    if any(type(r.get('id')) is not int or r['id'] <= 0 for r in referencias):
        raise ValueError('Las identidades de referencia deben ser enteros positivos.')
    if not referencias or len({r['id'] for r in referencias}) != len(referencias):
        raise ValueError('Se necesitan referencias únicas.')
    modelo = ClasificadorReferencias({r['id']: r['vector'] for r in referencias}, datos['modalidad'])
    consultas = datos['consultas']
    if not consultas:
        raise ValueError('Faltan consultas etiquetadas.')
    resultado = dict(origen=datos['origen'], consultas=len(consultas), conocidos=0, desconocidos=0,
                     aciertos=0, falsas_aceptaciones=0, falsos_rechazos=0, confusiones=0)
    for consulta in consultas:
        esperado = consulta['esperado']
        if esperado is not None and (type(esperado) is not int or esperado <= 0):
            raise ValueError('La identidad esperada debe ser un entero positivo o null.')
        if esperado is not None and esperado not in modelo.referencias:
            raise ValueError('Una identidad esperada no tiene referencia.')
        predicho = modelo.identificar(consulta['vector'], umbral=umbral, margen=margen).identidad
        resultado['conocidos' if esperado is not None else 'desconocidos'] += 1
        resultado['aciertos'] += int(predicho == esperado)
        resultado['falsas_aceptaciones'] += int(esperado is None and predicho is not None)
        resultado['falsos_rechazos'] += int(esperado is not None and predicho is None)
        resultado['confusiones'] += int(esperado is not None and predicho is not None and predicho != esperado)
    resultado['far'] = resultado['falsas_aceptaciones'] / resultado['desconocidos'] if resultado['desconocidos'] else None
    resultado['frr'] = resultado['falsos_rechazos'] / resultado['conocidos'] if resultado['conocidos'] else None
    return resultado


def calibrar(datos, max_far=0.01):
    if not 0 <= max_far <= 1:
        raise ValueError('FAR objetivo fuera de rango.')
    base = evaluar(datos)
    if min(base['conocidos'], base['desconocidos']) < 10:
        raise ValueError('La propuesta de calibración exige al menos 10 consultas conocidas y 10 desconocidas.')
    umbrales = [n / 100 for n in (range(30, 66, 5) if datos['modalidad'] == 'facial' else range(50, 96, 5))]
    candidatos = []
    for umbral in umbrales:
        for margen in (0.025, 0.05, 0.10):
            r = evaluar(datos, umbral=umbral, margen=margen)
            if r['far'] <= max_far and not r['confusiones']:
                candidatos.append({'umbral': umbral, 'margen': margen, **r})
    if not candidatos:
        return {'propuesta': None, 'motivo': 'Ningún ajuste satisface el objetivo en este conjunto.'}
    candidatos.sort(key=lambda r: (r['frr'], r['far'], -r['margen']))
    return {'propuesta': candidatos[0], 'advertencia': 'Propuesta sobre este conjunto; validar en datos independientes. No se aplica automáticamente.'}
