# agente.py
import operator
import os
import json
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.tools import tool
from langgraph.graph import StateGraph  # Quitamos END de aquí para evitar conflictos
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

# --- PASO 2: TOOLS (Criterio 3 + Bonus de Escalado) ---
@tool
def buscar_pedido(pedido_id: str) -> str:
    """Busca el estado de un pedido por su ID. Ejemplo: buscar_pedido('PED-1234')"""
    pedidos = {
        "PED-1234": {"estado": "enviado", "fecha_entrega": "15/05/2026", "total": 89.99},
        "PED-5678": {"estado": "en preparación", "fecha_entrega": "18/05/2026", "total": 45.50},
    }
    pedido = pedidos.get(pedido_id.upper())
    return str(pedido) if pedido else f"Pedido {pedido_id} no encontrado"

@tool
def calcular_reembolso(total: float, porcentaje: float) -> str:
    """Calcula el importe de un reembolso parcial."""
    reembolso = round(total * porcentaje / 100, 2)
    return f"Reembolso del {porcentaje}% sobre {total}€: {reembolso}€"

@tool
def escalar_a_humano(motivo: str) -> str:
    """Bonus: Registra el caso en un archivo JSON para que un operador humano tome el control."""
    caso = {"motivo": motivo, "estado": "pendiente_humano"}
    historial = []
    if os.path.exists("casos_humanos.json"):
        with open("casos_humanos.json", "r") as f:
            try:
                historial = json.load(f)
            except:
                pass
    historial.append(caso)
    with open("casos_humanos.json", "w") as f:
        json.dump(historial, f, indent=4)
    return "Caso escalado con éxito. Un agente humano se comunicará pronto."

tools = [buscar_pedido, calcular_reembolso, escalar_a_humano]

# --- PASO 3: CONFIGURACIÓN DEL GRAFO DE ESTADO (Criterio 4) ---
class EstadoSoporte(TypedDict):
    mensajes: Annotated[Sequence[BaseMessage], operator.add]

# Criterio 2: Configuración del Retriever para RAG de forma local
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectordb = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# Configuración del LLM Inteligente con Gemini
modelo = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
modelo_con_tools = modelo.bind_tools(tools)

def nodo_llm(estado: EstadoSoporte) -> dict:
    ultimo_humano = next(
        (m.content for m in reversed(estado["mensajes"]) if isinstance(m, HumanMessage)),
        ""
    )
    # RAG de políticas
    docs = retriever.invoke(ultimo_humano)
    contexto = "\n".join(d.page_content for d in docs)

    system = SystemMessage(content=f"""Eres un asistente de soporte amable y preciso.
Usa las herramientas disponibles para consultar pedidos, calcular reembolsos o escalar casos a humanos si el cliente está molesto.
Responde preguntas sobre políticas usando este contexto obtenido de la base de datos de la empresa:
{contexto}
Si no tienes información, dilo claramente. No inventes datos.""")

    mensajes_con_system = [system] + list(estado["mensajes"])
    respuesta = modelo_con_tools.invoke(mensajes_con_system)
    return {"mensajes": [respuesta]}

# LINEA 72 CORREGIDA: Devolvemos la cadena de texto estándar de finalización
def debe_continuar(estado: EstadoSoporte) -> str:
    ultimo = estado["mensajes"][-1]
    if hasattr(ultimo, "tool_calls") and ultimo.tool_calls:
        return "usar_tool"
    return "__end__" 

nodo_tools = ToolNode(tools)

grafo = StateGraph(EstadoSoporte)
grafo.add_node("llm", nodo_llm)
grafo.add_node("tools", nodo_tools)
grafo.set_entry_point("llm")

# LÍNEAS 87 Y 94 CORREGIDAS: Mapeamos explícitamente a la cadena de finalización estándar
grafo.add_conditional_edges(
    "llm", 
    debe_continuar, 
    {
        "usar_tool": "tools", 
        "__end__": "__end__"
    }
)

grafo.add_edge("tools", "llm")

# Criterio 4: Guardado de memoria por sesión (MemorySaver)
checkpointer = MemorySaver()
agente = grafo.compile(checkpointer=checkpointer)