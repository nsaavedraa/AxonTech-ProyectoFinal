"""
Punto de entrada del subscriber — HU_03.
Lee configuración desde variables de entorno y arranca el loop.
"""

import logging
import os

from src.subscriber import MQTTSubscriber, SubscriberConexionError
from src.validador import MensajeRecibido

logger = logging.getLogger("mqtt.main")


def procesar_mensaje(mensaje: MensajeRecibido) -> None:
    """
    Paso 6 del flujo básico: lógica de negocio post-recepción.
    Aquí va lo que el sistema debe hacer con el mensaje tras confirmarlo.
    """
    logger.info(f"[PROCESANDO] id={mensaje.id!r} categoria={mensaje.categoria!r}")
    # TODO: agregar lógica de negocio (guardar en DB, notificar, etc.)


def main():
    host = os.getenv("BROKER_HOST", "localhost")
    port = int(os.getenv("BROKER_PORT", "1883"))
    topic = os.getenv("TOPIC", "axon/mensajes/#")
    qos = int(os.getenv("QOS", "1"))
    client_id = os.getenv("CLIENT_ID", "subscriber_hu03")

    subscriber = MQTTSubscriber(
        host=host,
        port=port,
        topic=topic,
        qos=qos,
        client_id=client_id,
        on_mensaje_recibido=procesar_mensaje,
    )

    try:
        subscriber.iniciar()
    except SubscriberConexionError as e:
        logger.critical(f"[FATAL] {e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        logger.info("[SALIENDO] Interrupción de usuario.")
        subscriber.detener()


if __name__ == "__main__":
    main()
