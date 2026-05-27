# ingestar.py
import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
politicas_path = os.path.join(BASE_DIR, "politicas.txt")
chroma_path = os.path.join(BASE_DIR, "chroma_db")

try:
    loader = TextLoader(politicas_path, encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=chroma_path)

    print(f"Exito! Indexados {len(chunks)} chunks.")
except FileNotFoundError:
    print(f"Error: No se encontro el archivo '{politicas_path}'")
except Exception as e:
    print(f"Error al procesar documentos: {str(e)}")