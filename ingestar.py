# ingestar.py
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv  # <-- AÑADE ESTO

# Cargar la API Key desde el archivo .env automáticamente
load_dotenv()  # <-- AÑADE ESTO

loader = TextLoader("politicas.txt", encoding="utf-8")
docs = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = splitter.split_documents(docs)

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectordb = Chroma.from_documents(chunks, embeddings, persist_directory="./chroma_db")

print(f"Indexados {len(chunks)} chunks")