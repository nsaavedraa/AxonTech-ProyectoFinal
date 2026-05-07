"""
Subscriber MQTT — HU_03: Recepción de mensajes por el suscriptor
Implementa el flujo básico y los flujos alternos del caso de uso GU.HU3.UC1.
"""

import logging
import os
import time
from typing import Callable, Optional

import paho.mqtt.client as mqtt

from src.validador import (
    MensajeRecibido,
    MensajeInvalidoError,
    validar_payload,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("mqtt.subscriber")


class SubscriberConexionError(Exception):
    """Se lanza cuando no se puede establecer la conexión con el broker."""
    pass


class MQTTSubscriber:
    """
    Cliente suscriptor MQTT para HU_03.

    Implementa:
    - CA_01: recibir mensajes de una categoría de interés de forma íntegra.
    - CA_02: confirmar la recepción antes de continuar (QoS 1).
    - Flujos alternos: broker no disponible, mensaje inválido, suscriptor desconectado.
    """

    def __init__(
        self,
        host: str,
        port: int = 1883,
        topic: str = "axon/mensajes/#",
        qos: int = 1,
        client_id: str = "subscriber_hu03",
        on_mensaje_recibido: Optional[Callable[[MensajeRecibido], None]] = None,
        max_reintentos_conexion: int = 5,
    ):
        self.host = host
        self.port = port
        self.topic = topic
        self.qos = qos
        self.client_id = client_id
        self.on_mensaje_recibido = on_mensaje_recibido
        self.max_reintentos_conexion = max_reintentos_conexion

        self._conectado = False
        self._mensajes_recibidos: list[MensajeRecibido] = []
        self._errores: list[str] = []

        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe

    # ─────────────────────────────────────────────────────────────
    # Callbacks MQTT
    # ─────────────────────────────────────────────────────────────

    def _on_connect(self, client, userdata, flags, rc):
        """Paso 2-3 del flujo básico: validar conexión y suscribirse."""
        if rc == 0:
            self._conectado = True
            logger.info(f"[CONECTADO] Broker: {self.host}:{self.port}")
            # Paso 3: establecer comunicación — suscribirse al topic (CA_01)
            client.subscribe(self.topic, qos=self.qos)
        else:
            # Flujo alterno 3.1-3.3: no se puede establecer comunicación
            self._conectado = False
            motivo = {
                1: "Versión de protocolo incorrecta",
                2: "Identificador de cliente rechazado",
                3: "Servidor no disponible",
                4: "Usuario o contraseña incorrectos",
                5: "No autorizado",
            }.get(rc, f"Error desconocido (rc={rc})")
            logger.error(f"[ERROR CONEXIÓN] {motivo}")
            self._errores.append(f"conexion_fallida:{motivo}")

    def _on_disconnect(self, client, userdata, rc):
        """Flujo alterno 2.1-2.2: suscriptor desconectado."""
        self._conectado = False
        if rc != 0:
            logger.warning(f"[DESCONECTADO] Inesperado, rc={rc}. Paho reintentará.")
        else:
            logger.info("[DESCONECTADO] Desconexión limpia.")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Confirmación de suscripción exitosa."""
        logger.info(f"[SUSCRITO] Topic: {self.topic!r} | QoS concedido: {granted_qos}")

    def _on_message(self, client, userdata, msg):
        """
        Paso 4-5 del flujo básico: recibir y confirmar mensaje.

        Con QoS 1, paho-mqtt envía el PUBACK automáticamente al retornar
        este callback — cumpliendo CA_02 (confirmar recepción antes de
        continuar el proceso).
        """
        logger.info(f"[MENSAJE] Topic: {msg.topic!r} | QoS: {msg.qos} | {len(msg.payload)} bytes")

        # Paso 4: validar que el mensaje sea íntegro (CA_01)
        try:
            mensaje = validar_payload(msg.payload)
        except MensajeInvalidoError as e:
            # Flujo alterno 4.1-4.3: mensaje inválido — NO se debe procesar ni confirmar como OK
            logger.error(f"[MENSAJE INVÁLIDO] {e}")
            self._errores.append(f"mensaje_invalido:{e}")
            return  # No continuar (paso 4.3)

        # Paso 5: PUBACK enviado automáticamente por paho (QoS 1)
        logger.info(f"[RECIBIDO OK] {mensaje} — recepción confirmada al broker")
        self._mensajes_recibidos.append(mensaje)

        # Paso 6: continuar con el proceso siguiente
        if self.on_mensaje_recibido:
            try:
                self.on_mensaje_recibido(mensaje)
            except Exception as e:
                logger.error(f"[ERROR PROCESO] Error en callback de negocio: {e}")

    # ─────────────────────────────────────────────────────────────
    # API pública
    # ─────────────────────────────────────────────────────────────

    def conectar(self) -> None:
        """
        Establece conexión con el broker con reintentos.

        Raises:
            SubscriberConexionError: si no se puede conectar tras los reintentos.
        """
        for intento in range(1, self.max_reintentos_conexion + 1):
            try:
                logger.info(f"[CONECTANDO] Intento {intento}/{self.max_reintentos_conexion} → {self.host}:{self.port}")
                self.client.connect(self.host, self.port, keepalive=60)
                return
            except OSError as e:
                logger.warning(f"[REINTENTO] No se pudo conectar: {e}")
                if intento < self.max_reintentos_conexion:
                    time.sleep(2 ** intento)  # backoff exponencial

        raise SubscriberConexionError(
            f"No se pudo conectar al broker {self.host}:{self.port} "
            f"tras {self.max_reintentos_conexion} intentos."
        )

    def iniciar(self) -> None:
        """Inicia el loop bloqueante de escucha."""
        self.conectar()
        logger.info("[ESCUCHANDO] Loop MQTT iniciado...")
        self.client.loop_forever()

    def iniciar_en_background(self) -> None:
        """Inicia el loop en un hilo de fondo (útil para tests)."""
        self.conectar()
        self.client.loop_start()

    def detener(self) -> None:
        """Detiene el cliente limpiamente."""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("[DETENIDO] Subscriber desconectado.")

    @property
    def conectado(self) -> bool:
        return self._conectado

    @property
    def mensajes_recibidos(self) -> list[MensajeRecibido]:
        return list(self._mensajes_recibidos)

    @property
    def errores(self) -> list[str]:
        return list(self._errores)
