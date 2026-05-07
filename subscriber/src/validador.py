"""
Módulo de validación de mensajes MQTT — HU_03
Valida que el payload recibido sea íntegro y tenga la estructura esperada.
"""

import json
from dataclasses import dataclass
from typing import Any


class MensajeInvalidoError(Exception):
    """Se lanza cuando el mensaje recibido no cumple la estructura esperada."""
    pass


class MensajeVacioError(MensajeInvalidoError):
    """Se lanza cuando el payload está vacío."""
    pass


class MensajeNoEsJSONError(MensajeInvalidoError):
    """Se lanza cuando el payload no puede parsearse como JSON."""
    pass


class CampoRequeridoError(MensajeInvalidoError):
    """Se lanza cuando falta un campo obligatorio en el mensaje."""
    pass


@dataclass
class MensajeRecibido:
    """Representa un mensaje MQTT validado y decodificado."""
    id: str
    categoria: str
    contenido: Any
    timestamp: str
    raw: dict

    def __repr__(self):
        return f"MensajeRecibido(id={self.id!r}, categoria={self.categoria!r})"


CAMPOS_REQUERIDOS = {"id", "categoria", "contenido", "timestamp"}


def validar_payload(payload_bytes: bytes) -> MensajeRecibido:
    """
    Valida el payload raw de un mensaje MQTT.

    Args:
        payload_bytes: bytes recibidos del broker MQTT.

    Returns:
        MensajeRecibido con los campos decodificados.

    Raises:
        MensajeVacioError: si el payload está vacío.
        MensajeNoEsJSONError: si no es JSON válido.
        CampoRequeridoError: si falta algún campo obligatorio.
    """
    # Flujo alterno 4.1: mensaje vacío
    if not payload_bytes or not payload_bytes.strip():
        raise MensajeVacioError("El payload está vacío — no se puede procesar.")

    # Flujo alterno 4.1: JSON inválido
    try:
        data = json.loads(payload_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise MensajeNoEsJSONError(f"El payload no es JSON válido: {e}") from e

    # Verificar que sea un objeto (dict), no lista ni primitivo
    if not isinstance(data, dict):
        raise MensajeInvalidoError(
            f"El payload debe ser un objeto JSON, se recibió: {type(data).__name__}"
        )

    # Verificar campos requeridos
    faltantes = CAMPOS_REQUERIDOS - data.keys()
    if faltantes:
        raise CampoRequeridoError(
            f"Faltan campos obligatorios: {sorted(faltantes)}"
        )

    return MensajeRecibido(
        id=str(data["id"]),
        categoria=str(data["categoria"]),
        contenido=data["contenido"],
        timestamp=str(data["timestamp"]),
        raw=data,
    )
