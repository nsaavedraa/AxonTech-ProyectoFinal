"""
CAPA 1 — Pruebas Unitarias del Validador
Archivo: tests/test_capa1_validador.py

Prueba la lógica pura de validación de mensajes sin broker, sin red.
Técnicas: partición de equivalencia, análisis de valor límite, paramétricos.
"""

import json
import pytest

from src.validador import (
    validar_payload,
    MensajeRecibido,
    MensajeVacioError,
    MensajeNoEsJSONError,
    CampoRequeridoError,
    MensajeInvalidoError,
    CAMPOS_REQUERIDOS,
)


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

def payload_valido(**kwargs) -> bytes:
    """Genera un payload JSON válido, sobrescribiendo campos si se indica."""
    base = {
        "id": "msg-001",
        "categoria": "axon/mensajes/test",
        "contenido": "Mensaje de prueba",
        "timestamp": "2026-05-06T12:00:00",
    }
    base.update(kwargs)
    return json.dumps(base).encode()


# ─────────────────────────────────────────────────────────────
# V-01: Mensajes válidos — flujo básico (pasos 4-5 UC)
# ─────────────────────────────────────────────────────────────

class TestMensajesValidos:

    def test_V01_mensaje_completo_retorna_MensajeRecibido(self):
        """V-01-01: Payload completo con todos los campos → MensajeRecibido."""
        resultado = validar_payload(payload_valido())
        assert isinstance(resultado, MensajeRecibido)

    def test_V01_campos_mapeados_correctamente(self):
        """V-01-02: Los campos del JSON se mapean a los atributos del dataclass."""
        resultado = validar_payload(payload_valido(id="xyz-99", categoria="cat/test"))
        assert resultado.id == "xyz-99"
        assert resultado.categoria == "cat/test"
        assert resultado.contenido == "Mensaje de prueba"
        assert resultado.timestamp == "2026-05-06T12:00:00"

    def test_V01_contenido_puede_ser_objeto_anidado(self):
        """V-01-03: El campo 'contenido' acepta objetos JSON anidados."""
        resultado = validar_payload(
            payload_valido(contenido={"sensor": "temp", "valor": 23.5})
        )
        assert resultado.contenido == {"sensor": "temp", "valor": 23.5}

    def test_V01_contenido_puede_ser_lista(self):
        """V-01-04: El campo 'contenido' acepta listas."""
        resultado = validar_payload(payload_valido(contenido=[1, 2, 3]))
        assert resultado.contenido == [1, 2, 3]

    def test_V01_id_numerico_se_convierte_a_string(self):
        """V-01-05: Un id numérico se convierte a string sin error."""
        resultado = validar_payload(payload_valido(id=42))
        assert resultado.id == "42"

    def test_V01_raw_contiene_datos_originales(self):
        """V-01-06: El atributo 'raw' guarda el dict original completo."""
        resultado = validar_payload(payload_valido(extra_campo="ignorado"))
        assert "extra_campo" in resultado.raw

    @pytest.mark.parametrize("id_,categoria,contenido,timestamp", [
        ("msg-001", "axon/alertas",  "alerta crítica",     "2026-01-01T00:00:00"),
        ("msg-002", "axon/sensores", {"temp": 20},         "2026-06-15T08:30:00"),
        ("msg-003", "axon/logs",     ["entrada1"],         "2026-12-31T23:59:59"),
        ("a" * 100, "cat/larga",     "x",                  "2026-05-06T12:00:00"),
        ("msg-005", "c",             0,                    "2026-05-06T12:00:00"),
    ])
    def test_V01_parametricos_validos(self, id_, categoria, contenido, timestamp):
        """V-01-07 a V-01-11: Casos válidos paramétricos."""
        datos = {"id": id_, "categoria": categoria, "contenido": contenido, "timestamp": timestamp}
        resultado = validar_payload(json.dumps(datos).encode())
        assert isinstance(resultado, MensajeRecibido)


# ─────────────────────────────────────────────────────────────
# V-02: Payload vacío — flujo alterno 4.1-4.3
# ─────────────────────────────────────────────────────────────

class TestPayloadVacio:

    def test_V02_bytes_vacios_lanza_MensajeVacioError(self):
        """V-02-01: b'' lanza MensajeVacioError."""
        with pytest.raises(MensajeVacioError):
            validar_payload(b"")

    def test_V02_solo_espacios_lanza_MensajeVacioError(self):
        """V-02-02: b'   ' (solo espacios) lanza MensajeVacioError."""
        with pytest.raises(MensajeVacioError):
            validar_payload(b"   ")

    def test_V02_solo_newline_lanza_MensajeVacioError(self):
        """V-02-03: b'\\n\\t' lanza MensajeVacioError."""
        with pytest.raises(MensajeVacioError):
            validar_payload(b"\n\t")

    def test_V02_es_subclase_de_MensajeInvalidoError(self):
        """V-02-04: MensajeVacioError es subclase de MensajeInvalidoError."""
        with pytest.raises(MensajeInvalidoError):
            validar_payload(b"")


# ─────────────────────────────────────────────────────────────
# V-03: JSON inválido — flujo alterno 4.1-4.3
# ─────────────────────────────────────────────────────────────

class TestJSONInvalido:

    def test_V03_string_plano_lanza_MensajeNoEsJSONError(self):
        """V-03-01: 'texto plano' no es JSON → MensajeNoEsJSONError."""
        with pytest.raises(MensajeNoEsJSONError):
            validar_payload(b"texto plano")

    def test_V03_json_malformado_lanza_MensajeNoEsJSONError(self):
        """V-03-02: '{id: sin-comillas}' → MensajeNoEsJSONError."""
        with pytest.raises(MensajeNoEsJSONError):
            validar_payload(b"{id: sin-comillas}")

    def test_V03_json_truncado_lanza_MensajeNoEsJSONError(self):
        """V-03-03: JSON cortado a mitad → MensajeNoEsJSONError."""
        with pytest.raises(MensajeNoEsJSONError):
            validar_payload(b'{"id": "msg-001"')

    def test_V03_bytes_no_utf8_lanza_MensajeNoEsJSONError(self):
        """V-03-04: Bytes inválidos UTF-8 → MensajeNoEsJSONError."""
        with pytest.raises(MensajeNoEsJSONError):
            validar_payload(b"\xff\xfe invalido")

    def test_V03_array_json_lanza_MensajeInvalidoError(self):
        """V-03-05: Un array JSON (no objeto) → MensajeInvalidoError."""
        with pytest.raises(MensajeInvalidoError):
            validar_payload(b'["id", "msg-001"]')

    def test_V03_numero_json_lanza_MensajeInvalidoError(self):
        """V-03-06: Un número JSON → MensajeInvalidoError."""
        with pytest.raises(MensajeInvalidoError):
            validar_payload(b"42")

    @pytest.mark.parametrize("payload_bytes", [
        b"null",
        b"true",
        b"false",
        b'"solo un string"',
        b"{}[]",  # JSON seguido de más contenido
    ])
    def test_V03_parametricos_invalidos(self, payload_bytes):
        """V-03-07 a V-03-11: Payloads no-objeto paramétricos."""
        with pytest.raises(MensajeInvalidoError):
            validar_payload(payload_bytes)


# ─────────────────────────────────────────────────────────────
# V-04: Campos requeridos faltantes
# ─────────────────────────────────────────────────────────────

class TestCamposFaltantes:

    @pytest.mark.parametrize("campo_omitido", sorted(CAMPOS_REQUERIDOS))
    def test_V04_cada_campo_requerido_es_obligatorio(self, campo_omitido):
        """V-04-01 a V-04-04: Omitir cualquier campo requerido → CampoRequeridoError."""
        datos = {
            "id": "msg-001",
            "categoria": "cat/test",
            "contenido": "texto",
            "timestamp": "2026-05-06T12:00:00",
        }
        del datos[campo_omitido]
        with pytest.raises(CampoRequeridoError):
            validar_payload(json.dumps(datos).encode())

    def test_V04_objeto_vacio_lanza_CampoRequeridoError(self):
        """V-04-05: {} (objeto vacío) → CampoRequeridoError."""
        with pytest.raises(CampoRequeridoError):
            validar_payload(b"{}")

    def test_V04_mensaje_error_menciona_campos_faltantes(self):
        """V-04-06: El mensaje de error enumera los campos que faltan."""
        with pytest.raises(CampoRequeridoError) as exc_info:
            validar_payload(b'{"id": "x"}')
        assert "categoria" in str(exc_info.value)

    def test_V04_campos_extra_no_causan_error(self):
        """V-04-07: Campos adicionales no generan error (íntegro = tiene todo lo requerido)."""
        resultado = validar_payload(payload_valido(campo_extra="valor_extra"))
        assert isinstance(resultado, MensajeRecibido)


# ─────────────────────────────────────────────────────────────
# V-05: Valor límite del payload
# ─────────────────────────────────────────────────────────────

class TestValorLimite:

    def test_V05_payload_1_byte_json_invalido(self):
        """V-05-01: Payload de 1 byte → MensajeNoEsJSONError."""
        with pytest.raises(MensajeNoEsJSONError):
            validar_payload(b"{")

    def test_V05_contenido_string_largo_es_valido(self):
        """V-05-02: Contenido de 10.000 caracteres es válido."""
        resultado = validar_payload(payload_valido(contenido="x" * 10_000))
        assert len(resultado.contenido) == 10_000
