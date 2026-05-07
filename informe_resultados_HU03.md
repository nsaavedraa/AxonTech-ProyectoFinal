# Informe de Resultados de Pruebas
## STR — HU_03 Recepción de mensajes MQTT

| Campo | Valor |
|-------|-------|
| ID Informe | STR-HU03-2026 |
| Referencia al Plan | PDP-HU03-2026 |
| Fecha de ejecución | 2026-05-07 15:26:27 (UTC-5) |
| Ejecutado por | Claude Code |
| Entorno | Docker · Python 3.11.15 · paho-mqtt 1.6.1 |
| Veredicto final | **PASSED** |

---

## Resumen ejecutivo

Se ejecutaron 50 casos de prueba distribuidos en dos capas: 35 unitarios sobre el módulo `validador.py` (sin broker) y 15 de integración con broker Mosquitto real en contenedor Docker. La totalidad de los casos resultó en estado PASSED, alcanzando y superando los umbrales de cobertura definidos en el plan (validador.py 100 %, subscriber.py 85 %).

---

## Métricas globales

| Métrica | Resultado | Umbral del plan | Estado |
|---------|-----------|-----------------|--------|
| Casos ejecutados | 50 | 50 | ✓ |
| Casos PASSED | 50 | 50 | ✓ |
| Casos FAILED | 0 | 0 | ✓ |
| Cobertura validador.py | 100% | ≥ 90% | ✓ |
| Cobertura subscriber.py | 85% | ≥ 80% | ✓ |
| Duración total | 56.35s | — | — |

---

## Resultados por capa

### Capa 1 — Unitarios (test_capa1_validador.py)

| ID | Descripción | Estado | Duración |
|----|-------------|--------|----------|
| V-01-01 | Mensaje completo retorna MensajeRecibido | PASSED | < 0.01s |
| V-01-02 | Campos mapeados correctamente en MensajeRecibido | PASSED | < 0.01s |
| V-01-03 | Contenido puede ser objeto JSON anidado | PASSED | < 0.01s |
| V-01-04 | Contenido puede ser lista JSON | PASSED | < 0.01s |
| V-01-05 | ID numérico se convierte a string | PASSED | < 0.01s |
| V-01-06 | Raw contiene bytes originales del payload | PASSED | < 0.01s |
| V-01-07 | Mensaje válido paramétrico — msg-001, axon/alertas | PASSED | < 0.01s |
| V-01-08 | Mensaje válido paramétrico — msg-002, axon/sensores | PASSED | < 0.01s |
| V-01-09 | Mensaje válido paramétrico — msg-003, axon/logs | PASSED | < 0.01s |
| V-01-10 | Mensaje válido paramétrico — ID de 98 caracteres | PASSED | < 0.01s |
| V-01-11 | Mensaje válido paramétrico — categoría y contenido mínimos | PASSED | < 0.01s |
| V-02-01 | Payload de bytes vacíos lanza MensajeVacioError | PASSED | < 0.01s |
| V-02-02 | Payload de solo espacios lanza MensajeVacioError | PASSED | < 0.01s |
| V-02-03 | Payload de solo newline lanza MensajeVacioError | PASSED | < 0.01s |
| V-02-04 | MensajeVacioError es subclase de MensajeInvalidoError | PASSED | < 0.01s |
| V-03-01 | String plano lanza MensajeNoEsJSONError | PASSED | < 0.01s |
| V-03-02 | JSON malformado lanza MensajeNoEsJSONError | PASSED | < 0.01s |
| V-03-03 | JSON truncado lanza MensajeNoEsJSONError | PASSED | < 0.01s |
| V-03-04 | Bytes no-UTF8 lanzan MensajeNoEsJSONError | PASSED | < 0.01s |
| V-03-05 | Array JSON lanza MensajeInvalidoError | PASSED | < 0.01s |
| V-03-06 | Número JSON lanza MensajeInvalidoError | PASSED | < 0.01s |
| V-03-07 | JSON primitivo inválido: null | PASSED | < 0.01s |
| V-03-08 | JSON primitivo inválido: true | PASSED | < 0.01s |
| V-03-09 | JSON primitivo inválido: false | PASSED | < 0.01s |
| V-03-10 | JSON primitivo inválido: "solo un string" | PASSED | < 0.01s |
| V-03-11 | JSON malformado compuesto: {}[] | PASSED | < 0.01s |
| V-04-01 | Campo requerido obligatorio: categoria | PASSED | < 0.01s |
| V-04-02 | Campo requerido obligatorio: contenido | PASSED | < 0.01s |
| V-04-03 | Campo requerido obligatorio: id | PASSED | < 0.01s |
| V-04-04 | Campo requerido obligatorio: timestamp | PASSED | < 0.01s |
| V-04-05 | Objeto JSON vacío lanza CampoRequeridoError | PASSED | < 0.01s |
| V-04-06 | Mensaje de error menciona los campos faltantes | PASSED | < 0.01s |
| V-04-07 | Campos adicionales no causan error de validación | PASSED | < 0.01s |
| V-05-01 | Payload de 1 byte es JSON inválido | PASSED | < 0.01s |
| V-05-02 | Contenido string de 10.000 caracteres es válido | PASSED | < 0.01s |

**Subtotal Capa 1:** 35 PASSED / 0 FAILED — Duración: 0.15s

---

### Capa 2 — Integración (test_capa2_integracion.py)

| ID | Descripción | Estado | Duración |
|----|-------------|--------|----------|
| I-01-01 | Subscriber se conecta al broker Mosquitto | PASSED | 0.50s |
| I-01-02 | Subscriber queda suscrito al topic configurado | PASSED | 2.51s |
| I-02-01 | Mensaje recibido es íntegro (CA_01) | PASSED | 2.51s |
| I-02-02 | Solo recibe mensajes del topic suscrito | PASSED | 2.51s |
| I-02-03 | Wildcard recibe mensajes de subtopics | PASSED | 2.51s |
| I-02-04 | Múltiples mensajes recibidos en orden | PASSED | 5.33s |
| I-03-01 | QoS 1 garantiza entrega del mensaje (CA_02) | PASSED | 2.51s |
| I-03-02 | No se registran errores en recepción válida | PASSED | 2.51s |
| I-04-01 | Mensaje no-JSON no se procesa | PASSED | 2.51s |
| I-04-02 | Mensaje sin campos requeridos no se procesa | PASSED | 2.51s |
| I-04-03 | Payload vacío no se procesa | PASSED | 2.51s |
| I-04-04 | Mensaje inválido no bloquea mensajes posteriores | PASSED | 3.31s |
| I-05-01 | Conexión a host inexistente lanza SubscriberConexionError | PASSED | 2.82s |
| I-05-02 | Conexión a puerto incorrecto lanza SubscriberConexionError | PASSED | < 0.01s |
| I-05-03 | Mensaje de error menciona host y puerto involucrados | PASSED | 4.01s |

**Subtotal Capa 2:** 15 PASSED / 0 FAILED — Duración: 54.01s

---

## Cobertura de código

| Módulo | Líneas totales | Líneas cubiertas | Cobertura | Umbral | Estado |
|--------|---------------|-----------------|-----------|--------|--------|
| src/validador.py | 34 | 34 | 100% | 90% | ✓ |
| src/subscriber.py | 89 | 76 | 85% | 80% | ✓ |

> **Nota:** Las líneas no cubiertas de `subscriber.py` corresponden a las ramas de error interno del bucle de red de paho-mqtt (líneas 83-92, 98, 131-134, 155, 164-166) que sólo se activarían ante fallos de protocolo de bajo nivel no reproducibles en entorno de prueba. Esto no implica defecto en la lógica de negocio.

---

## Desviaciones respecto al plan

Ninguna. La ejecución se realizó conforme al plan PDP-HU03-2026.

---

## Defectos encontrados

No se registraron defectos durante esta ejecución.

---

## Conclusión y recomendación

El componente subscriber MQTT cumple los criterios de salida definidos en el plan PDP-HU03-2026. Se recomienda proceder con la integración al pipeline CI y avanzar a la siguiente historia de usuario.

---
*Generado por Claude Code · Referencia: PDP-HU03-2026 · ISO/IEC/IEEE 29119-3:2021*
