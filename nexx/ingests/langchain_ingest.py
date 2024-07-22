import logging
import os

from langchain.indexes import SQLRecordManager, index
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.utils.html import PREFIXES_TO_IGNORE_REGEX, SUFFIXES_TO_IGNORE_REGEX
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings

from future.loaders.langchain_loader import LangchainDocsLoader, LangsmithDocsLoader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_embeddings_model() -> Embeddings:
    return OllamaEmbeddings(model="nomic-embed-text")


def ingest_docs():
    DATABASE_HOST = "127.0.0.1"
    DATABASE_PORT = "3306"
    DATABASE_USERNAME = "root"
    DATABASE_PASSWORD = "admin@123"
    DATABASE_NAME = "chatbot"
    RECORD_MANAGER_DB_URL = f"mysql+mysqlconnector://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    COLLECTION_NAME = "langchain"

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    embedding = get_embeddings_model()

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embedding,
    )

    record_manager = SQLRecordManager(
        f"pingan_health/{COLLECTION_NAME}", db_url=RECORD_MANAGER_DB_URL
    )
    record_manager.create_schema()

    langchain_docs_loader = LangchainDocsLoader()
    docs_from_documentation = langchain_docs_loader.load_langchain_docs()
    logger.info(f"Loaded {len(docs_from_documentation)} docs from documentation")

    langsmith_docs_loader = LangsmithDocsLoader()
    docs_from_langsmith = langsmith_docs_loader.load_langsmith_docs()
    logger.info(f"Loaded {len(docs_from_langsmith)} docs from Langsmith")

    docs_transformed = text_splitter.split_documents(
        docs_from_documentation + docs_from_langsmith
    )
    docs_transformed = [doc for doc in docs_transformed if len(doc.page_content) > 10]

    for doc in docs_transformed:
        if "source" not in doc.metadata:
            doc.metadata["source"] = ""
        if "title" not in doc.metadata:
            doc.metadata["title"] = ""

    indexing_stats = index(
        docs_transformed,
        record_manager,
        vectorstore,
        cleanup="full",
        source_id_key="source",
        force_update=(os.environ.get("FORCE_UPDATE") or "false").lower() == "true",
    )

    logger.info(f"Indexing stats: {indexing_stats}")


if __name__ == "__main__":
    ingest_docs()
