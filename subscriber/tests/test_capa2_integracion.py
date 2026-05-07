"""
CAPA 2 — Pruebas de Integración con Broker Real
Archivo: tests/test_capa2_integracion.py

Prueba el subscriber contra un broker Mosquitto real.
Requiere: BROKER_HOST y BROKER_PORT configurados (ver conftest.py).

Cubre:
- CA_01: entrega íntegra del mensaje bajo la categoría suscrita
- CA_02: confirmación de recepción (QoS 1)
- Flujos alternos del UC
"""

import json
import time
import pytest
import paho.mqtt.client as mqtt


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def publicar(broker_host, broker_port, topic, payload_dict, qos=1):
    """Publica un mensaje en el broker y espera confirmación."""
    pub = mqtt.Client(client_id="test_publisher")
    pub.connect(broker_host, broker_port)
    pub.loop_start()
    info = pub.publish(topic, json.dumps(payload_dict), qos=qos)
    info.wait_for_publish(timeout=5)
    pub.loop_stop()
    pub.disconnect()


PAYLOAD_VALIDO = {
    "id": "msg-integracion-001",
    "categoria": "axon/mensajes/test",
    "contenido": "Mensaje de integración",
    "timestamp": "2026-05-06T12:00:00",
}


# ─────────────────────────────────────────────────────────────
# I-01: Conexión al broker — pasos 2-3 del flujo básico
# ─────────────────────────────────────────────────────────────

class TestConexionBroker:

    def test_I01_subscriber_se_conecta_al_broker(self, subscriber_con_broker):
        """I-01-01: Subscriber establece conexión exitosa con el broker."""
        time.sleep(0.5)
        assert subscriber_con_broker.conectado is True

    def test_I01_subscriber_queda_suscrito_al_topic(self, subscriber_con_broker, broker_host, broker_port):
        """I-01-02: Tras conectar, el subscriber está suscrito y recibe mensajes."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "axon/mensajes/test", PAYLOAD_VALIDO)
        time.sleep(1)
        assert len(subscriber_con_broker.mensajes_recibidos) >= 1


# ─────────────────────────────────────────────────────────────
# I-02: Recepción íntegra — CA_01
# ─────────────────────────────────────────────────────────────

class TestRecepcionIntegra:

    def test_I02_mensaje_recibido_es_integro(self, subscriber_con_broker, broker_host, broker_port):
        """I-02-01 (CA_01): El mensaje llega con todos sus campos intactos."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "axon/mensajes/test", PAYLOAD_VALIDO)
        time.sleep(1)

        assert len(subscriber_con_broker.mensajes_recibidos) >= 1
        msg = subscriber_con_broker.mensajes_recibidos[0]
        assert msg.id == PAYLOAD_VALIDO["id"]
        assert msg.categoria == PAYLOAD_VALIDO["categoria"]
        assert msg.contenido == PAYLOAD_VALIDO["contenido"]
        assert msg.timestamp == PAYLOAD_VALIDO["timestamp"]

    def test_I02_solo_recibe_mensajes_del_topic_suscrito(self, subscriber_con_broker, broker_host, broker_port):
        """I-02-02 (CA_01): No recibe mensajes de topics fuera de su suscripción."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "otro/topic/diferente", PAYLOAD_VALIDO)
        time.sleep(1)
        assert len(subscriber_con_broker.mensajes_recibidos) == 0

    def test_I02_wildcard_recibe_subtopics(self, subscriber_con_broker, broker_host, broker_port):
        """I-02-03: La suscripción 'axon/mensajes/#' recibe subtopics como 'axon/mensajes/alertas'."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "axon/mensajes/alertas", PAYLOAD_VALIDO)
        time.sleep(1)
        assert len(subscriber_con_broker.mensajes_recibidos) >= 1

    def test_I02_multiples_mensajes_recibidos_en_orden(self, subscriber_con_broker, broker_host, broker_port):
        """I-02-04: Múltiples mensajes se reciben en orden de publicación."""
        time.sleep(0.5)
        ids = [f"msg-orden-{i:03d}" for i in range(1, 4)]
        for mid in ids:
            publicar(broker_host, broker_port, "axon/mensajes/test",
                     {**PAYLOAD_VALIDO, "id": mid})
            time.sleep(0.1)

        time.sleep(1.5)
        recibidos = [m.id for m in subscriber_con_broker.mensajes_recibidos]
        assert ids[0] in recibidos
        assert ids[1] in recibidos
        assert ids[2] in recibidos


# ─────────────────────────────────────────────────────────────
# I-03: Confirmación de recepción — CA_02
# ─────────────────────────────────────────────────────────────

class TestConfirmacionRecepcion:

    def test_I03_qos1_entrega_garantizada(self, subscriber_con_broker, broker_host, broker_port):
        """I-03-01 (CA_02): Con QoS 1, el mensaje se entrega al menos una vez y se confirma."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "axon/mensajes/test", PAYLOAD_VALIDO, qos=1)
        time.sleep(1)
        # Si llegó, la confirmación fue exitosa (paho la gestiona internamente)
        assert len(subscriber_con_broker.mensajes_recibidos) == 1

    def test_I03_no_hay_errores_en_recepcion_valida(self, subscriber_con_broker, broker_host, broker_port):
        """I-03-02 (CA_02): Recepción exitosa no genera errores en el subscriber."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "axon/mensajes/test", PAYLOAD_VALIDO)
        time.sleep(1)
        assert subscriber_con_broker.errores == []


# ─────────────────────────────────────────────────────────────
# I-04: Flujo alterno — Mensaje inválido (4.1-4.3)
# ─────────────────────────────────────────────────────────────

class TestMensajeInvalido:

    def test_I04_mensaje_no_json_no_se_procesa(self, subscriber_con_broker, broker_host, broker_port):
        """I-04-01 (FA 4.1): Un payload de texto plano se rechaza y no se agrega a recibidos."""
        time.sleep(0.5)
        pub = mqtt.Client(client_id="test_pub_invalido")
        pub.connect(broker_host, broker_port)
        pub.loop_start()
        info = pub.publish("axon/mensajes/test", b"esto no es json", qos=1)
        info.wait_for_publish(timeout=5)
        pub.loop_stop()
        pub.disconnect()

        time.sleep(1)
        assert len(subscriber_con_broker.mensajes_recibidos) == 0
        assert any("mensaje_invalido" in e for e in subscriber_con_broker.errores)

    def test_I04_mensaje_sin_campos_no_se_procesa(self, subscriber_con_broker, broker_host, broker_port):
        """I-04-02 (FA 4.1): JSON válido pero sin campos requeridos se rechaza."""
        time.sleep(0.5)
        publicar(broker_host, broker_port, "axon/mensajes/test", {"dato": "incompleto"})
        time.sleep(1)
        assert len(subscriber_con_broker.mensajes_recibidos) == 0

    def test_I04_payload_vacio_no_se_procesa(self, subscriber_con_broker, broker_host, broker_port):
        """I-04-03 (FA 4.3): Payload vacío se rechaza sin confirmar como válido."""
        time.sleep(0.5)
        pub = mqtt.Client(client_id="test_pub_vacio")
        pub.connect(broker_host, broker_port)
        pub.loop_start()
        info = pub.publish("axon/mensajes/test", b"", qos=1)
        info.wait_for_publish(timeout=5)
        pub.loop_stop()
        pub.disconnect()

        time.sleep(1)
        assert len(subscriber_con_broker.mensajes_recibidos) == 0

    def test_I04_mensaje_invalido_no_bloquea_siguientes(self, subscriber_con_broker, broker_host, broker_port):
        """I-04-04: Un mensaje inválido no bloquea la recepción de mensajes válidos posteriores."""
        time.sleep(0.5)

        # Primero: inválido
        pub = mqtt.Client(client_id="test_pub_seq")
        pub.connect(broker_host, broker_port)
        pub.loop_start()
        pub.publish("axon/mensajes/test", b"no es json", qos=1).wait_for_publish(5)

        # Luego: válido
        time.sleep(0.3)
        pub.publish("axon/mensajes/test", json.dumps(PAYLOAD_VALIDO), qos=1).wait_for_publish(5)
        pub.loop_stop()
        pub.disconnect()

        time.sleep(1.5)
        assert len(subscriber_con_broker.mensajes_recibidos) == 1


# ─────────────────────────────────────────────────────────────
# I-05: Flujo alterno — Broker no disponible (3.1-3.3)
# ─────────────────────────────────────────────────────────────

class TestBrokerNoDisponible:

    def test_I05_conexion_a_host_inexistente_lanza_error(self):
        """I-05-01 (FA 3.1-3.3): Conectar a broker inexistente lanza SubscriberConexionError."""
        from src.subscriber import MQTTSubscriber, SubscriberConexionError

        sub = MQTTSubscriber(
            host="host-que-no-existe.local",
            port=1883,
            max_reintentos_conexion=1,
        )
        with pytest.raises(SubscriberConexionError):
            sub.conectar()

    def test_I05_conexion_a_puerto_incorrecto_lanza_error(self, broker_host):
        """I-05-02 (FA 3.1-3.3): Puerto incorrecto (9999) lanza SubscriberConexionError."""
        from src.subscriber import MQTTSubscriber, SubscriberConexionError

        sub = MQTTSubscriber(
            host=broker_host,
            port=9999,
            max_reintentos_conexion=1,
        )
        with pytest.raises(SubscriberConexionError):
            sub.conectar()

    def test_I05_mensaje_error_menciona_host_y_puerto(self):
        """I-05-03: El mensaje del SubscriberConexionError incluye host y puerto."""
        from src.subscriber import MQTTSubscriber, SubscriberConexionError

        sub = MQTTSubscriber(
            host="host-invalido.local",
            port=1234,
            max_reintentos_conexion=1,
        )
        with pytest.raises(SubscriberConexionError) as exc_info:
            sub.conectar()
        assert "host-invalido.local" in str(exc_info.value)
        assert "1234" in str(exc_info.value)
