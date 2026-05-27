# ingestar.py
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

try:
    print("Leyendo las politicas de la empresa...")
    loader = TextLoader("politicas.txt", encoding="utf-8")
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    print("Generando embeddings locales con HuggingFace...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("Guardando vectores en ChromaDB...")
    vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

    print(f"Indexados {len(chunks)} chunks en ChromaDB.")

except Exception as e:
    print(f"Error al procesar documentos: {str(e)}")