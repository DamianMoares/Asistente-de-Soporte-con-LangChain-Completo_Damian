import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage
from agente import agente

app = FastAPI(
    title="Asistente de Soporte con IA",
    description="API de asistente de soporte powered by LangChain y Gemini",
    version="1.0.0"
)

class MensajeRequest(BaseModel):
    session_id: str = Field(..., description="ID único de la sesión del usuario")
    mensaje: str = Field(..., description="Mensaje del usuario")

@app.get("/")
def health_check():
    """Verifica que el servidor está funcionando correctamente."""
    return {"status": "ok", "mensaje": "Asistente de Soporte con IA corriendo"}

@app.post("/chat")
def chat(request: MensajeRequest):
    """Procesa un mensaje del usuario y retorna la respuesta del asistente."""
    try:
        if not request.mensaje.strip():
            raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
        
        config = {"configurable": {"thread_id": request.session_id}}
        resultado = agente.invoke(
            {"mensajes": [HumanMessage(content=request.mensaje)]},
            config=config
        )
        return {"respuesta": resultado["mensajes"][-1].content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar mensaje: {str(e)}")

@app.get("/chat/{session_id}/historial")
def obtener_historial(session_id: str):
    """Obtiene el historial de conversación de una sesión."""
    try:
        config = {"configurable": {"thread_id": session_id}}
        estado_actual = agente.get_state(config)
        if not estado_actual.values or "mensajes" not in estado_actual.values:
            return {"historial": []}
        historial = [{"rol": msg.type, "contenido": msg.content} for msg in estado_actual.values["mensajes"]]
        return {"historial": historial}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")

@app.delete("/chat/{session_id}")
def limpiar_sesion(session_id: str):
    """Limpia la sesión de un usuario."""
    return {"mensaje": f"Sesión {session_id} cerrada"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
