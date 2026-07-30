import pytest
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.form_AskEmail import ValidatePedirEmailForm

def test_validar_correo_correcto():
    # 1. PREPARACIÓN (Arrange)
    validador = ValidatePedirEmailForm()
    dispatcher = CollectingDispatcher()
    
    # Creamos un "tracker falso" simulando que el usuario envió un correo y tiene 0 intentos
    tracker_falso = Tracker(
        sender_id="usuario_prueba",
        slots={"intentos_email": 0},
        latest_message={},
        events=[],
        paused=False,
        followup_action=None,
        active_loop={},
        latest_action_name="action_listen"
    )

    correo_ingresado = "correo@correo.com"

    # 2. EJECUCIÓN (Act)
    # Llamamos a tu función pasándole los datos simulados
    resultado = validador.validate_email_usuario(
        slot_value=correo_ingresado,
        dispatcher=dispatcher,
        tracker=tracker_falso,
        domain={}
    )

    # 3. VERIFICACIÓN (Assert)
    # Comprobamos que el resultado sea exactamente lo que esperamos
    assert resultado == {"email_usuario": "correo@correo.com", "intentos_email": 0}

def test_validar_correo_ivalido():
    validador = ValidatePedirEmailForm()
    dispatcher = CollectingDispatcher()

    tracker_falso = Tracker(
        sender_id="usuario_prueba",
        slots={"intentos_email": 0},
        latest_message={},
        events=[],
        paused=False,
        followup_action=None,
        active_loop={},
        latest_action_name="active_listen"
    )

    correo_ingresado = "correo errado"

    resultado = validador.validate_email_usuario(
        slot_value=correo_ingresado,
        dispatcher=dispatcher,
        tracker=tracker_falso,
        domain={}
    )

    assert resultado == {"email_usuario": None, "intentos_email":1}

def test_validar_correo_limite_intentos():
    validador = ValidatePedirEmailForm()
    dispatcher = CollectingDispatcher()

    tracker_falso = Tracker(
        sender_id="usuario_prueba",
        slots={"intentos_email":2},
        latest_message={},
        events=[],
        paused=False,
        followup_action=None,
        active_loop={},
        latest_action_name="action_listen"
    )

    correo_ingresado = "Tercer intento malo"

    resultado = validador.validate_email_usuario(
        slot_value=correo_ingresado,
        dispatcher=dispatcher,
        tracker=tracker_falso,
        domain={}
    )

    assert resultado == {
        "email_usuario": "cancelado_por_intentos",
        "intentos_email": 0
    }