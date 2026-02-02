import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


DOCUMENT_PATH = "data/tactics"
CHROMA_PATH = "vector_db"


def ingest_documents():
    loader = DirectoryLoader(DOCUMENT_PATH, glob="*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    vector_db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)

if __name__ == "__main__":
    ingest_documents()