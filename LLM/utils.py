import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
load_dotenv()

db_file = os.path.join(os.path.dirname(__file__), "real_estate.db")
table_name = "properties"             

df = pd.read_csv('realtor-data.csv')

db_conn = sqlite3.connect(db_file)
cursor = db_conn.cursor()

df.to_sql(table_name, db_conn, if_exists="replace", index=False)

# Check table creation success and count records
cursor.execute(f"SELECT COUNT(*) FROM {table_name}")

def show_all_tables() -> list[str]:
    cursor = db_conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

    tables = cursor.fetchall()
    return [t[0] for t in tables]

def list_table_info(table_name: str) -> list[tuple[str, str]]:

    cursor = db_conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name});")

    schema = cursor.fetchall()
    
    return [(col[1], col[2]) for col in schema]

def formatear_respuesta(data, consulta):
    if not data:
        return "No se encontraron resultados."

    if "city" in data[0] and "total" in data[0]:
        respuesta = "Ciudades con más propiedades según tu consulta:\n\n"
        for i, row in enumerate(data, 1):
            respuesta += f"{i}. {row['city']}: {row['total']} propiedades\n"
        return respuesta

    elif "state" in data[0] and "avg_price" in data[0]:
        respuesta = "Promedio de precios por estado:\n\n"
        for row in data:
            respuesta += f"- {row['state']}: ${round(row['avg_price'], 2):,.0f}\n"
        return respuesta

    keys = data[0].keys()
    table = "| " + " | ".join(keys) + " |\n"
    table += "| " + " | ".join("---" for _ in keys) + " |\n"
    for row in data:
        table += "| " + " | ".join(str(row[k]) for k in keys) + " |\n"
    return table

def query(sql: str) -> str:
    cursor = db_conn.cursor()
    cursor.execute(sql)

    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    data = [dict(zip(columns, row)) for row in rows]

    return formatear_respuesta(data, sql)


api_key = os.getenv("GOOGLE_API_KEY")
prompt = """
 Eres un chatbot que responde preguntas usando una base de datos SQL de bienes raíces.

 Instrucciones:
 1. Cuando respondas la primera pregunta, inicia con un saludo amigable (ej. "Hola, con gusto te ayudo.").
 2. Siempre termina tu respuesta con una frase como "¿Necesitas otra consulta?".

 Tu flujo de trabajo:
 1. Recibe preguntas en lenguaje natural.
 2. Usa las herramientas disponibles:
    - `show_all_tables`: para ver las tablas disponibles.
    - `list_table_info`: para conocer las columnas de una tabla.
    - `query`: para ejecutar una consulta SQL y obtener los datos.
 3. Responde al usuario de forma clara, útil y en lenguaje natural.
 4. No repitas datos crudos si puedes resumirlos.
 5. Nunca traduzcas los nombres de las tablas o columnas. Usa siempre los nombres reales de la base de datos, como 'properties'.

 Ejemplos:
 - Usuario: ¿Qué ciudad tiene más casas por debajo de $400,000?
   Tú: (usa `query` para contar propiedades con precio < 400000, agrupa por ciudad y ordena descendente)

 - Usuario: ¿Cuál es el promedio de precio por estado?
   Tú: (usa `query` para agrupar por estado y calcular el promedio de precio)

 - Usuario: ¿Dónde hay más propiedades de lujo?
   Tú: (usa `query` para filtrar por propiedades con precio > 1,000,000, agrupa por ciudad o estado)

 Siempre que tengas dudas sobre el esquema, usa `list_table_info`.
 """
db_tools = [show_all_tables, list_table_info, query]

client = genai.Client(api_key=api_key)

class RealEstateChatBot:
    def __init__(self, prompt, tools, model="gemini-2.0-flash-lite-001"):
        self.prompt = prompt
        self.tools = tools
        self.model = model
        self.first_turn = True
        self.chat = client.chats.create(
            model=self.model,
            config=types.GenerateContentConfig(
                system_instruction=self.prompt,
                tools=self.tools,
            ),
        )

    def send(self, message: str) -> str:
        response = self.chat.send_message(message)
        reply = response.text.strip()

        if self.first_turn:
            greeting = "Hola! 👋 Con gusto te ayudo. "
            self.first_turn = False
        else:
            greeting = ""

        # Evita duplicar el cierre
        if "¿Necesitas otra consulta?" not in reply:
            reply += " ¿Necesitas otra consulta?"

        return f"{greeting}{reply}"