# AxonTech — Proyecto Final

Plataforma IoT para recepción y procesamiento de mensajes MQTT. Cubre los casos de uso definidos en las historias de usuario del proyecto AxonTech.

## Estructura del repositorio

```
AxonTech-ProyectoFinal/
├── broker/
│   └── mosquitto.conf                   ← Configuración del broker Mosquitto
├── documents/
│   ├── HU01/
│   │   └── GU.HU1.UC1.docx              ← Especificación del caso de uso HU01
│   ├── HU03/
│   │   ├── GU_HU3_UC1.docx              ← Especificación del caso de uso HU03
│   │   ├── STP-HU03-2026.docx           ← Plan de pruebas HU03
│   │   └── STR-HU03-2026.docx           ← Reporte de resultados HU03
│   └── lineamientos/
│       └── Redacción Historias de usuario.docx
├── subscriber/
│   ├── src/
│   │   ├── validador.py                 ← CAPA 1: validación pura del payload
│   │   ├── subscriber.py                ← CAPA 2: cliente MQTT + callbacks
│   │   └── main.py                      ← Punto de entrada con config de entorno
│   ├── tests/
│   │   ├── test_capa1_validador.py      ← 35 tests unitarios (sin broker)
│   │   └── test_capa2_integracion.py    ← 15 tests de integración (con broker)
│   ├── conftest.py
│   ├── pytest.ini
│   ├── requirements.txt
│   └── Dockerfile
├── docker-compose.yml
└── informe_resultados_HU03.md           ← Resumen de ejecución de pruebas
```

## Historias de usuario

| HU | Caso de uso | Documentación | Estado |
|----|-------------|---------------|--------|
| HU_01 | GU.HU1.UC1 | [documents/HU01/](documents/HU01/) | En desarrollo |
| HU_03 | GU.HU3.UC1 — Recepción de mensajes por el suscriptor | [documents/HU03/](documents/HU03/) | Completado ✓ |

---

## HU_03 — Recepción de mensajes por el suscriptor

Sistema subscriber MQTT que implementa el caso de uso GU.HU3.UC1.

### Inicio rápido

#### 1. Levantar broker + subscriber

```bash
docker-compose up --build
```

#### 2. Publicar un mensaje de prueba (terminal separada)

```bash
docker-compose run --rm publisher
```

O directamente con mosquitto_pub si lo tenés instalado:

```bash
mosquitto_pub -h localhost -t axon/mensajes/test \
  -m '{"id":"msg001","categoria":"axon/mensajes/test","contenido":"Hola","timestamp":"2026-05-06T12:00:00"}' \
  -q 1
```

#### 3. Ejecutar las pruebas

```bash
# Solo Capa 1 (no necesita broker):
docker-compose run --rm tests pytest tests/test_capa1_validador.py -v

# Solo Capa 2 (necesita broker levantado):
docker-compose up -d broker
docker-compose run --rm tests pytest tests/test_capa2_integracion.py -v

# Todo con cobertura:
docker-compose run --rm tests
```

#### 4. Ejecutar tests localmente (sin Docker)

```bash
cd subscriber
pip install -r requirements.txt

# Capa 1 (sin broker):
pytest tests/test_capa1_validador.py -v

# Capa 2 (con broker local en puerto 1883):
BROKER_HOST=localhost pytest tests/test_capa2_integracion.py -v
```

### Variables de entorno

| Variable     | Default         | Descripción                        |
|--------------|------------------|------------------------------------|
| BROKER_HOST  | localhost        | Host del broker MQTT               |
| BROKER_PORT  | 1883             | Puerto del broker                  |
| TOPIC        | axon/mensajes/#  | Topic al que suscribirse           |
| QOS          | 1                | Nivel de calidad de servicio (0-2) |
| CLIENT_ID    | subscriber_hu03  | ID del cliente MQTT                |

### Mapeo con el caso de uso GU.HU3.UC1

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

### Resultados de pruebas

| Capa | Tests | Resultado | Cobertura |
|------|-------|-----------|-----------|
| Capa 1 — Validación | 35 | PASSED ✓ | validador.py: 100% |
| Capa 2 — Integración | 15 | PASSED ✓ | subscriber.py: 85% |

Ver reporte completo en [informe_resultados_HU03.md](informe_resultados_HU03.md).

### Alternativa en nube (Azure Free Tier)

1. **Azure Container Apps** — desplegá el subscriber como container
2. **Azure Event Grid** (MQTT Broker) — gratis hasta 100.000 operaciones/mes
3. Ajustá `BROKER_HOST` al namespace de Event Grid y agregá TLS en el subscriber

Ver: https://learn.microsoft.com/azure/event-grid/mqtt-overview
