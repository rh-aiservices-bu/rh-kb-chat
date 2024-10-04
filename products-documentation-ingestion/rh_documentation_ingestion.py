import os
from langchain_openai import OpenAIEmbeddings
from langchain_milvus import Milvus
import rh_documentation_processing as rhdp


os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"


def ingest_documentation(product_info, milvus_endpoint, embeddings_endpoint):
    """Ingest documentation into Milvus"""

    EMBEDDINGS_API_URL = embeddings_endpoint["EMBEDDINGS_API_URL"]
    EMBEDDINGS_API_KEY = embeddings_endpoint["EMBEDDINGS_API_KEY"]

    MILVUS_HOST = milvus_endpoint["MILVUS_HOST"]
    MILVUS_PORT = milvus_endpoint["MILVUS_PORT"]
    MILVUS_USERNAME = milvus_endpoint["MILVUS_USERNAME"]
    MILVUS_PASSWORD = milvus_endpoint["MILVUS_PASSWORD"]
    MILVUS_COLLECTION = f"{product_info.product}_{product_info.language}_{product_info.version}".replace(
        "-", "_"
    ).replace(
        ".", "_"
    )
    # Replace needed because Milvus collection names cannot contain hyphens or periods

    splits = rhdp.generate_splits(
        product_info.product,
        product_info.product_full_name,
        product_info.version,
        product_info.language,
    )

    # Here we use Nomic AI's Nomic Embed Text model to generate embeddings
    # Adapt to your liking
    model_kwargs = {"trust_remote_code": True, "device": "cuda"}
    embeddings = OpenAIEmbeddings(
        openai_api_base=EMBEDDINGS_API_URL,
        openai_api_key=EMBEDDINGS_API_KEY,
        model="nomic-embed-text-v1.5",
        chunk_size="16",
        show_progress_bar=True
    )

    vector_store = Milvus(
        embedding_function=embeddings,
        connection_args={
            "host": MILVUS_HOST,
            "port": MILVUS_PORT,
            "user": MILVUS_USERNAME,
            "password": MILVUS_PASSWORD,
        },
        collection_name=MILVUS_COLLECTION,
        enable_dynamic_field=True,
        text_field="page_content",
        auto_id=True,
        drop_old=True,
    )

    print(f"Calculating embeddings and uploading documents to collection {MILVUS_COLLECTION}")

    vector_store.add_documents(splits, batch_size=32)

    print("Finished!")
