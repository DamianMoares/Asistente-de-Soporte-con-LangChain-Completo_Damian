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
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

load_dotenv()

# Obtener la ruta base del directorio del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- HERRAMIENTAS ---
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
    if porcentaje < 0 or porcentaje > 100:
        return "Error: El porcentaje debe estar entre 0 y 100"
    reembolso = round(total * porcentaje / 100, 2)
    return f"Reembolso del {porcentaje}% sobre {total}€: {reembolso}€"

@tool
def escalar_a_humano(motivo: str) -> str:
    """Registra el caso en el sistema para que un agente humano tome el control."""
    try:
        caso = {"motivo": motivo, "estado": "pendiente_humano"}
        historial = []
        casos_path = os.path.join(BASE_DIR, "casos_humanos.json")
        
        if os.path.exists(casos_path):
            with open(casos_path, "r", encoding="utf-8") as f:
                try:
                    historial = json.load(f)
                except json.JSONDecodeError:
                    historial = []
        
        historial.append(caso)
        with open(casos_path, "w", encoding="utf-8") as f:
            json.dump(historial, f, indent=4, ensure_ascii=False)
        return "Caso escalado con éxito. Un agente humano se comunicará pronto."
    except Exception as e:
        return f"Error al escalar caso: {str(e)}"

tools = [buscar_pedido, calcular_reembolso, escalar_a_humano]

# --- CONFIGURACIÓN DEL GRAFO ---
class EstadoSoporte(TypedDict):
    mensajes: Annotated[Sequence[BaseMessage], operator.add]

# Embeddings locales gratuitos (offline, sin API key)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
chroma_path = os.path.join(BASE_DIR, "chroma_db")
vectordb = Chroma(persist_directory=chroma_path, embedding_function=embeddings)
retriever = vectordb.as_retriever(search_kwargs={"k": 3})

# Usamos Gemini 2.0 Flash (gratuito en AI Studio)
modelo = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
modelo_con_tools = modelo.bind_tools(tools)

def nodo_llm(estado: EstadoSoporte) -> dict:
    ultimo_humano = next(
        (m.content for m in reversed(estado["mensajes"]) if isinstance(m, HumanMessage)),
        ""
    )
    docs = retriever.invoke(ultimo_humano)
    contexto = "\n".join(d.page_content for d in docs)

    system = SystemMessage(content=f"""Eres un asistente de soporte amable y preciso.
Usa las herramientas disponibles para consultar pedidos, calcular reembolsos o escalar casos.
Responde preguntas sobre políticas usando exclusivamente este contexto:
{contexto}
Si no tienes información en el contexto o mediante herramientas, di claramente que no la tienes. No inventes datos.""")

    mensajes_con_system = [system] + list(estado["mensajes"])
    respuesta = modelo_con_tools.invoke(mensajes_con_system)
    return {"mensajes": [respuesta]}

def debe_continuar(estado: EstadoSoporte) -> str:
    ultimo = estado["mensajes"][-1]
    if hasattr(ultimo, "tool_calls") and ultimo.tool_calls:
        return "usar_tool"
    return END

nodo_tools = ToolNode(tools)

grafo = StateGraph(EstadoSoporte)
grafo.add_node("llm", nodo_llm)
grafo.add_node("tools", nodo_tools)
grafo.set_entry_point("llm")
grafo.add_conditional_edges("llm", debe_continuar, {"usar_tool": "tools", END: END})
grafo.add_edge("tools", "llm")

checkpointer = MemorySaver()
agente = grafo.compile(checkpointer=checkpointer)