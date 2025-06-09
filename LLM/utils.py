import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

table_name = "properties"

# Obtiene la ruta raíz del proyecto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Ruta segura a la base de datos
db_file = os.path.join(BASE_DIR, "real_estate.db")

# Ruta segura al archivo CSV (ajusta si tu CSV está en otra carpeta)
csv_path = os.path.join(BASE_DIR, "LLM", "realtor-data.csv")

# Cargar el DataFrame
df = pd.read_csv(csv_path)

# Crear tabla si no existe (solo aquí se hace la conexión globalmente porque es un paso inicial único)
with sqlite3.connect(db_file) as conn:
    df.to_sql(table_name, conn, if_exists="replace", index=False)

# Función: Mostrar todas las tablas de la base de datos
def show_all_tables():
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tablas = cursor.fetchall()
    return tablas

# Función: Obtener esquema de una tabla
def list_table_info(table_name: str) -> list[tuple[str, str]]:
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema = cursor.fetchall()
    return [(col[1], col[2]) for col in schema]

# Función: Formatear la respuesta del bot
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

# Función: Ejecutar consultas SQL
def query(sql: str) -> str:
    with sqlite3.connect(db_file) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        data = [dict(zip(columns, row)) for row in rows]
    return formatear_respuesta(data, sql)


api_key = os.getenv("GOOGLE_API_KEY")
prompt = """
 Eres un chatbot amable y eficiente que responde preguntas sobre una base de datos SQL de bienes raíces.

Tu objetivo:
Responde directamente a las preguntas del usuario usando datos de la base de datos, con un tono amigable pero sin explicaciones técnicas innecesarias.

Reglas:
1. Solo saluda en la **primera respuesta de la conversación**. Usa algo breve como:  
   "¡Hola! 👋 Con gusto te ayudo."
2. No expliques cómo estás haciendo la consulta ni menciones nombres de columnas como `bedrooms` o `price`, a menos que el usuario lo pida.
3. Si el usuario no especifica una tabla, asume que se refiere a `properties`.
4. Si una pregunta es ambigua, intenta adivinar el significado de forma lógica y responde lo mejor posible. Si no puedes, pide una aclaración breve.
5. Usa las funciones disponibles:
   - `show_all_tables`
   - `list_table_info`
   - `query`
6. Da siempre respuestas claras y naturales, como lo haría una persona.
7. Termina cada respuesta con: **"¿Necesitas otra consulta?"**

Ejemplos:
- Usuario: ¿Qué ciudad tiene más casas por debajo de $400,000?
  → Houston es la ciudad con más casas por debajo de $400,000, con un total de 4414. ¿Necesitas otra consulta?

- Usuario: ¿En qué ciudad hay más habitaciones en promedio?
  → Los Angeles tiene el promedio más alto de habitaciones por propiedad: 4.2. ¿Necesitas otra consulta?

- Usuario: ¿Dónde hay más casas en venta?
  → La ciudad con más casas en venta es Phoenix, con 5320 propiedades. ¿Necesitas otra consulta?
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

        # Evita saludo duplicado
        if self.first_turn:
            self.first_turn = False
            if "hola" not in reply.lower():
                reply = f"¡Hola! 👋 Con gusto te ayudo. {reply}"

        # Agrega cierre si falta
        if "¿necesitas otra consulta?" not in reply.lower():
            reply = f"{reply.rstrip('.')} ¿Necesitas otra consulta?"

        return reply
