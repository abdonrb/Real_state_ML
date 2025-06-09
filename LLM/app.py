import streamlit as st
from utils import (show_all_tables, list_table_info, query, RealEstateChatBot)

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
bot = RealEstateChatBot(prompt, db_tools)

# ----- TÍTULO -----
st.markdown("<h1 style='text-align: center;'>💬 Chatbot Inmobiliario</h1>", unsafe_allow_html=True)

# ----- SESIÓN -----
if "history" not in st.session_state:
    st.session_state.history = []

# ----- ENTRADA -----
user_input = st.chat_input("Escribe tu consulta...")

if user_input:
    response = bot.send(user_input)
    st.session_state.history.append(("user", user_input))
    st.session_state.history.append(("bot", response))

# ----- ESTILO DE CONVERSACIÓN -----
for role, text in st.session_state.history:
    if role == "user":
        st.markdown(
            f"""
            <div style='text-align: right; margin: 10px 0;'>
                <span style='background-color: #DCF8C6; color: #000; padding: 10px 15px; 
                             border-radius: 15px; display: inline-block; max-width: 80%;'>
                    {text}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style='text-align: left; margin: 10px 0;'>
                <span style='background-color: #F1F0F0; color: #000; padding: 10px 15px; 
                             border-radius: 15px; display: inline-block; max-width: 80%;'>
                    {text}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
