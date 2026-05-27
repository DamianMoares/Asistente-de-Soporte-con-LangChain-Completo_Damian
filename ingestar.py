# ingestar.py
import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings # Modelos de Google
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

# Obtener la ruta base del script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
politicas_path = os.path.join(BASE_DIR, "politicas.txt")
chroma_path = os.path.join(BASE_DIR, "chroma_db")

try:
    loader = TextLoader(politicas_path, encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # Usamos los embeddings gratuitos de Google (Genera vectores de 768 dimensiones)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=chroma_path)

    print(f"✅ ¡Éxito! Indexados {len(chunks)} chunks de forma gratuita con Gemini.")
except FileNotFoundError:
    print(f"❌ Error: No se encontró el archivo '{politicas_path}'")
except Exception as e:
    print(f"❌ Error al procesar documentos: {str(e)}")