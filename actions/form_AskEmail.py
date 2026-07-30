import re
from typing import Text, List, Any, Dict
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict

# --- CLASE 1: SOLO VALIDA EL DATO ---
class ValidatePedirEmailForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_pedir_email_form"

    def validate_email_usuario(
        self, slot_value: Any, dispatcher: CollectingDispatcher, tracker: Tracker, domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        patron_correo = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        es_correo_valido = re.match(patron_correo, str(slot_value))
        intentos = tracker.get_slot("intentos_email") or 0

        if es_correo_valido:
            # Éxito: Guardamos el correo y reseteamos intentos
            return {"email_usuario": slot_value, "intentos_email": 0}
        else:
            # Fallo: Aumentamos el contador
            nuevos_intentos = intentos + 1
            
            if nuevos_intentos >= 3:
                # Al tercer fallo, nos rendimos y enviamos el mensaje de cancelación
                dispatcher.utter_message(response="utter_cancel_email_request")
                # Llenamos el slot con un texto cualquiera para forzar el cierre del formulario
                return {"email_usuario": "cancelado_por_intentos", "intentos_email": 0}
            
            # ¡IMPORTANTE! Solo rechazamos el slot, NO enviamos mensajes aquí.
            return {"email_usuario": None, "intentos_email": nuevos_intentos}

# --- CLASE 2: SOLO HACE LA PREGUNTA DINÁMICA ---
class ActionAskEmailUsuario(Action):
    def name(self) -> Text:
        # Este nombre es mágico. Rasa lo buscará automáticamente porque el slot se llama 'email_usuario'
        return "action_ask_email_usuario"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[Dict[Text, Any]]:
        # Leemos cuántos intentos lleva el usuario
        intentos = tracker.get_slot("intentos_email") or 0

        # Disparamos el mensaje correcto según el intento
        if intentos == 0:
            dispatcher.utter_message(response="utter_ask_email_results")
        elif intentos == 1:
            dispatcher.utter_message(response="utter_ask_email_results_second")
        elif intentos == 2:
            dispatcher.utter_message(response="utter_ask_email_results_format")

        return []