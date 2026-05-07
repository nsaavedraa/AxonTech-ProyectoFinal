"""
conftest.py — Fixtures compartidas para todas las capas de prueba.
"""

import os
import time
import pytest

from src.subscriber import MQTTSubscriber


# ─────────────────────────────────────────────────────────────
# Configuración del broker (de variables de entorno o defaults)
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def broker_host() -> str:
    return os.getenv("BROKER_HOST", "localhost")


@pytest.fixture(scope="session")
def broker_port() -> int:
    return int(os.getenv("BROKER_PORT", "1883"))


# ─────────────────────────────────────────────────────────────
# Fixture: subscriber conectado (Capa 2)
# Crea un subscriber fresco por cada test para aislamiento.
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def subscriber_con_broker(broker_host, broker_port):
    """
    Subscriber real conectado al broker para cada test.
    Se crea, conecta en background y se destruye limpiamente al finalizar.
    """
    sub = MQTTSubscriber(
        host=broker_host,
        port=broker_port,
        topic="axon/mensajes/#",
        qos=1,
        client_id=f"test_subscriber_{time.time_ns()}",  # único por test
        max_reintentos_conexion=3,
    )
    sub.iniciar_en_background()
    time.sleep(0.5)  # dar tiempo a que se conecte y suscriba

    yield sub

    sub.detener()
    time.sleep(0.2)
