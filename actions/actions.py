import os
import glob
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()
KNOWLEDGE_DIR = "./knowledge_base"
chroma_client = None
collection = None
apikey = os.getenv("OPENAI_API_KEY")


def inicializar_rag():
    global chroma_client, collection
    api_key = apikey
    if not api_key:
        print("ADVERTENCIA: La variable de entorno OPENAI_API_KEY no está configurada.")
        return

    try:
        # Inicializar cliente de Chroma en memoria
        chroma_client = chromadb.EphemeralClient()
        
        # Configurar la función de embeddings de OpenAI
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name="text-embedding-3-small"
        )
        
        # Crear o recuperar colección
        collection = chroma_client.get_or_create_collection(
            name="aws_ai_knowledge",
            embedding_function=openai_ef
        )

        if not os.path.exists(KNOWLEDGE_DIR):
            os.makedirs(KNOWLEDGE_DIR)
            with open(os.path.join(KNOWLEDGE_DIR, "ejemplo.txt"), "w", encoding="utf-8") as f:
                f.write("AWS Certified AI Practitioner es una certificación de nivel básico diseñada para validar tu conocimiento en IA y ML.")

        # Cargar y dividir archivos
        documentos = []
        ids = []
        metadatas = []
        doc_id = 1

        files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.txt"))
        for file_path in files:
            with open(file_path, "r", encoding="utf-8") as f:
                contenido = f.read()
                # División simple por párrafos/líneas dobles para fragmentar
                parrafos = [p.strip() for p in contenido.split("\n\n") if p.strip()]
                for p in parrafos:
                    documentos.append(p)
                    ids.append(f"doc_{doc_id}")
                    metadatas.append({"source": os.path.basename(file_path)})
                    doc_id += 1

        if documentos:
            # Guardar en Chroma
            collection.add(
                documents=documentos,
                ids=ids,
                metadatas=metadatas
            )
            print(f"RAG inicializado correctamente con {len(documentos)} fragmentos.")
    except Exception as e:
        print(f"Error durante la inicialización de RAG: {str(e)}")

# Intentar inicializar si la API key ya está cargada al arrancar
inicializar_rag()

class ActionResponderRAG(Action):
    def name(self) -> Text:
        return "action_responder_rag"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        query = tracker.latest_message.get("text")
        api_key = apikey
       
        if not api_key:
            dispatcher.utter_message(text="Error: La variable de entorno 'OPENAI_API_KEY' no está configurada. Por favor configúrala antes de usar RAG.")
            return []

        global collection
        # Inicializar al vuelo si no se hizo al inicio por falta de API key
        if collection is None:
            try:
                inicializar_rag()
            except Exception as e:
                dispatcher.utter_message(text=f"Error al inicializar la base de datos vectorial: {str(e)}")
                return []

        if collection is None or collection.count() == 0:
            dispatcher.utter_message(text="La base de conocimientos está vacía o no se pudo cargar. Asegúrate de colocar archivos .txt en la carpeta 'knowledge_base'.")
            return []

        try:
            # Buscar en Chroma
            results = collection.query(
                query_texts=[query],
                n_results=3
            )

            # Obtener el contexto de los documentos encontrados
            docs_encontrados = results.get("documents", [[]])[0]
            contexto = "\n\n".join(docs_encontrados)

            if not contexto:
                dispatcher.utter_message(text="No encontré información relevante en la base de conocimientos para responder a tu pregunta.")
                return []

            # Llamar a OpenAI usando el cliente estándar
            client = OpenAI(api_key=api_key)
            prompt = f"""Usa la siguiente información de contexto para responder la pregunta del usuario. 
Si no sabes la respuesta o no está en el contexto, di amablemente que no posees esa información.

Contexto:
{contexto}

Pregunta del usuario: {query}
Respuesta:"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Eres un asistente de estudio experto en la certificación AWS Certified AI Practitioner."},
                    {"role": "user", "content": prompt},
                    {""}
                ],
                temperature=0.2
            )

            respuesta_generada = response.choices[0].message.content.strip()
            dispatcher.utter_message(text=respuesta_generada)

        except Exception as e:
            dispatcher.utter_message(text=f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}")

        return []