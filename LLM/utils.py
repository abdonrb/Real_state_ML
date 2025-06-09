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
 Eres un chatbot que responde preguntas usando una base de datos SQL de bienes raíces.

Objetivo:
Responder preguntas del usuario en lenguaje natural, utilizando las herramientas disponibles para consultar una base de datos SQL.

Instrucciones de interacción:
1. Siempre comienza con un saludo amigable como: "¡Hola! Con gusto te ayudo."
2. Siempre termina tu respuesta con: "¿Necesitas otra consulta?"
3. Si el usuario no menciona el nombre de la tabla, asume que se trata de la tabla 'properties' (tabla principal).
4. Si el usuario hace una pregunta ambigua, intenta deducir la intención. Si no es posible, pide una aclaración concreta.
5. Usa las funciones `show_all_tables`, `list_table_info` y `query` para razonar tu respuesta.
6. Nunca traduzcas los nombres de columnas o tablas. Usa los nombres reales como `properties`, `price`, `city`, `state`, `bedrooms`, etc.
7. No repitas datos crudos si puedes resumirlos o hacerlos más comprensibles.
 Herramientas disponibles:

- `show_all_tables`: muestra las tablas disponibles.
- `list_table_info`: muestra las columnas de una tabla.
- `query`: ejecuta una consulta SQL y devuelve los resultados.

 Ejemplos de uso:
- Usuario: ¿Qué ciudad tiene más casas por debajo de $400,000?
  Tú: (Usa `query` para contar propiedades con `price < 400000`, agrupa por `city` y ordena descendente)

- Usuario: ¿Cuál es el promedio de precio por estado?
  Tú: (Usa `query` para agrupar por `state` y calcular el promedio de `price`)

- Usuario: ¿Dónde hay más propiedades de lujo?
  Tú: (Filtra propiedades con `price > 1000000`, agrupa por `city` o `state`)

- Usuario: ¿En qué ciudad hay más casas en venta?
  Tú: (Agrupa por `city` y cuenta cuántas propiedades hay en cada una)

En caso de duda sobre columnas disponibles, usa `list_table_info('properties')`.

Tu misión es ser útil, flexible y natural al hablar.
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