# HU_03 — Recepción de mensajes por el suscriptor (MQTT)

Sistema subscriber MQTT que implementa el caso de uso GU.HU3.UC1.

## Estructura del proyecto

```
mqtt-subscriber/
├── broker/
│   └── mosquitto.conf          ← Configuración del broker Mosquitto
├── subscriber/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── validador.py        ← CAPA 1: validación pura del payload
│   │   ├── subscriber.py       ← CAPA 2: cliente MQTT + callbacks
│   │   └── main.py             ← Punto de entrada con config de entorno
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_capa1_validador.py    ← Tests unitarios (sin broker)
│   │   └── test_capa2_integracion.py ← Tests de integración (con broker)
│   ├── conftest.py             ← Fixtures compartidas
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml
```

## Inicio rápido

### 1. Levantar broker + subscriber

```bash
docker-compose up --build
```

### 2. Publicar un mensaje de prueba (terminal separada)

```bash
docker-compose run --rm publisher
```

O directamente con mosquitto_pub si lo tenés instalado:

```bash
mosquitto_pub -h localhost -t axon/mensajes/test \
  -m '{"id":"msg001","categoria":"axon/mensajes/test","contenido":"Hola","timestamp":"2026-05-06T12:00:00"}' \
  -q 1
```

### 3. Ejecutar las pruebas

```bash
# Solo Capa 1 (no necesita broker):
docker-compose run --rm tests pytest tests/test_capa1_validador.py -v

# Solo Capa 2 (necesita broker levantado):
docker-compose up -d broker
docker-compose run --rm tests pytest tests/test_capa2_integracion.py -v

# Todo con cobertura:
docker-compose run --rm tests
```

### 4. Ejecutar tests localmente (sin Docker)

```bash
cd subscriber
pip install -r requirements.txt

# Capa 1 (sin broker):
pytest tests/test_capa1_validador.py -v

# Capa 2 (con broker local en puerto 1883):
BROKER_HOST=localhost pytest tests/test_capa2_integracion.py -v
```

## Variables de entorno

| Variable      | Default              | Descripción                        |
|--------------|----------------------|------------------------------------|
| BROKER_HOST  | localhost            | Host del broker MQTT               |
| BROKER_PORT  | 1883                 | Puerto del broker                  |
| TOPIC        | axon/mensajes/#      | Topic al que suscribirse           |
| QOS          | 1                    | Nivel de calidad de servicio (0-2) |
| CLIENT_ID    | subscriber_hu03      | ID del cliente MQTT                |

## Mapeo con el caso de uso GU.HU3.UC1

| Paso UC | Código |
|---------|--------|
| Paso 1: broker distribuye → sistema recibe notificación | `_on_message` callback |
| Paso 2: validar que el suscriptor esté conectado | `_on_connect` con rc==0 |
| Paso 3: establecer comunicación | `client.connect()` + `client.subscribe()` |
| Paso 4: recibir mensaje íntegro | `validar_payload()` |
| Paso 5: confirmar recepción | QoS 1 — PUBACK automático de paho |
| Paso 6: continuar con el proceso | `on_mensaje_recibido` callback |
| FA 3.1-3.3: broker no disponible | `SubscriberConexionError` con reintentos |
| FA 4.1-4.3: mensaje inválido | `MensajeInvalidoError` — no se confirma |
| FE 2.1-2.2: suscriptor desconectado | `_on_disconnect` con rc != 0 |

## Alternativa en nube (Azure Free Tier)

Si preferís no usar Docker local:

1. **Azure Container Apps** — desplegá el subscriber como container
2. **Azure Event Grid** (MQTT Broker) — gratis hasta 100.000 operaciones/mes
3. Ajustá `BROKER_HOST` al namespace de Event Grid y agregá TLS en el subscriber

Ver: https://learn.microsoft.com/azure/event-grid/mqtt-overview
