# 🏡 Real Estate AI Assistant

Este proyecto combina análisis de datos, machine learning y un chatbot potenciado por un modelo LLM para ayudar a los usuarios a explorar datos inmobiliarios de forma natural y conversacional.

---

## 📊 ¿Qué hace este proyecto?

- Realiza un análisis exploratorio de datos (EDA) sobre un dataset de propiedades en EE.UU.
- Entrena modelos de machine learning (XGBoost) para predecir el precio de las viviendas.
- Implementa un asistente virtual basado en LLM que responde preguntas en lenguaje natural sobre la base de datos inmobiliaria.
- Proporciona una interfaz amigable tipo WhatsApp desarrollada con **Streamlit**.

---

## ⚙️ Tecnologías utilizadas

- Python
- Pandas, Matplotlib, Seaborn (EDA)
- Scikit-learn, XGBoost (ML)
- Google Generative AI (`genai`)
- Streamlit (interfaz)
- SQL (consultas)
- `.env` para manejo seguro de claves

---

## 🧠 Componentes del proyecto

| Módulo | Descripción |
|--------|-------------|
| `Eda.ipynb` | Exploración y visualización de datos del mercado inmobiliario. |
| `XGBoost.ipynb` | Entrenamiento de modelo predictivo para estimar precios. |
| `llm.py` | Chatbot conectado a la base de datos con lógica para responder en lenguaje natural. |
| `utils.py` | Funciones SQL y de integración para `show_all_tables`, `query`, etc. |
| `app.py` | Interfaz web conversacional para interacción con el asistente. |

---

## 💬 ¿Cómo funciona el chatbot?

El chatbot responde preguntas como:

- ¿Qué ciudad tiene más casas por debajo de $400,000?
- ¿Dónde hay más propiedades de lujo?
- ¿Cuál es el precio promedio por estado?

Usa herramientas SQL para obtener los datos, y responde con lenguaje natural. Está diseñado para:

- Saludar solo al inicio
- Responder con amabilidad, sin repetir detalles técnicos
- Sugerir nuevas consultas al final de cada respuesta

---
