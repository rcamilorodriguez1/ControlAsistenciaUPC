from datetime import datetime, timezone
from zoneinfo import ZoneInfo


ZONA_HORARIA_COLOMBIA = ZoneInfo("America/Bogota")


def hora_actual_colombia():
    return datetime.now(ZONA_HORARIA_COLOMBIA)


def convertir_a_hora_colombia(fecha_hora):
    if isinstance(fecha_hora, str):
        fecha_hora = datetime.fromisoformat(fecha_hora)

    if fecha_hora.tzinfo is None:
        fecha_hora = fecha_hora.replace(tzinfo=timezone.utc)

    return fecha_hora.astimezone(ZONA_HORARIA_COLOMBIA)
