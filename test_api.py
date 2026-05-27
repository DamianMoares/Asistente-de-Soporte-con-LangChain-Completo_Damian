#!/usr/bin/env python3
"""
Ejemplos de uso de la API del Asistente de Soporte
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Prueba el endpoint de salud"""
    print("\n✅ Probando health check...")
    response = requests.get(f"{BASE_URL}/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_chat_pedido():
    """Prueba consulta sobre un pedido"""
    print("\n✅ Probando consulta de pedido...")
    payload = {
        "session_id": "usuario_test_123",
        "mensaje": "¿Cuál es el estado de mi pedido PED-1234?"
    }
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_chat_politicas():
    """Prueba consulta sobre políticas"""
    print("\n✅ Probando consulta de políticas...")
    payload = {
        "session_id": "usuario_test_123",
        "mensaje": "¿Cuáles son las políticas de devolución?"
    }
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_chat_reembolso():
    """Prueba cálculo de reembolso"""
    print("\n✅ Probando cálculo de reembolso...")
    payload = {
        "session_id": "usuario_test_123",
        "mensaje": "Necesito un reembolso del 20% sobre 100 euros"
    }
    response = requests.post(
        f"{BASE_URL}/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_historial():
    """Obtiene el historial de una sesión"""
    print("\n✅ Obteniendo historial de sesión...")
    response = requests.get(f"{BASE_URL}/chat/usuario_test_123/historial")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_limpiar_sesion():
    """Limpia una sesión"""
    print("\n✅ Limpiando sesión...")
    response = requests.delete(f"{BASE_URL}/chat/usuario_test_123")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def main():
    """Ejecuta todos los tests"""
    print("=" * 60)
    print("PRUEBAS DE API - Asistente de Soporte con IA")
    print("=" * 60)
    
    try:
        test_health()
        test_chat_pedido()
        test_chat_politicas()
        test_chat_reembolso()
        test_historial()
        test_limpiar_sesion()
        
        print("\n" + "=" * 60)
        print("✅ ¡Todas las pruebas completadas!")
        print("=" * 60)
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: No se puede conectar al servidor.")
        print("Asegúrate de que la API está ejecutándose en http://localhost:8000")
        print("Ejecuta: python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    main()
