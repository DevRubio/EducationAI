import os
import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from dotenv import load_dotenv

load_dotenv()

class ActionLlamarApi(Action):
    def name(self) -> Text:
        return "action_llamar_api"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        url = os.getenv("URL_API")

        try:
            respuesta = requests.get(url)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                title = datos.get("title")
                description = datos.get("description")

                mensaje = f"!Datos obtenidos de forma correcta title: {title} Description: {description}"
            else:
                mensaje = "Hubo un error al consultar la API Intenta mas tarde"
        except Exception as e:
            mensaje = f"Error de conexion con la API: {str(e)}"
        dispatcher.utter_message(text=mensaje)

        return []