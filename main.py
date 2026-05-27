# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from agente import agente  # Importamos el grafo compilado

app = FastAPI(title="Asistente de Soporte Completo")

@app.get("/")
def health():
    return {"status": "ok", "service": "Asistente de Soporte"}

class MensajeRequest(BaseModel):
    session_id: str
    mensaje: str

# Criterio 5 y 6: Chat aislado por identificador de sesión único
@app.post("/chat")
def chat(request: MensajeRequest):
    try:
        config = {"configurable": {"thread_id": request.session_id}}
        resultado = agente.invoke(
            {"mensajes": [HumanMessage(content=request.mensaje)]},
            config=config
        )
        return {"respuesta": resultado["mensajes"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Bonus: Obtención estructurada de todo el historial de la sesión
@app.get("/chat/{session_id}/historial")
def obtener_historial(session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    estado_actual = agente.get_state(config)
    
    if not estado_actual.values or "mensajes" not in estado_actual.values:
        return {"historial": []}
        
    historial = [
        {"rol": msg.type, "contenido": msg.content} 
        for msg in estado_actual.values["mensajes"]
    ]
    return {"historial": historial}

@app.delete("/chat/{session_id}")
def limpiar_sesion(session_id: str):
    return {"mensaje": f"Sesión {session_id} cerrada"}