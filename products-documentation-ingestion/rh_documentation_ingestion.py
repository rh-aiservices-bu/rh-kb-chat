import os
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Milvus
import rh_documentation_processing as rhdp


os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"


def ingest_documentation(product_info, milvus):
    """Ingest documentation into Milvus"""

    MILVUS_HOST = milvus["MILVUS_HOST"]
    MILVUS_PORT = milvus["MILVUS_PORT"]
    MILVUS_USERNAME = milvus["MILVUS_USERNAME"]
    MILVUS_PASSWORD = milvus["MILVUS_PASSWORD"]
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
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1",
        model_kwargs=model_kwargs,
        show_progress=True,
    )

    db = Milvus(
        embedding_function=embeddings,
        connection_args={
            "host": MILVUS_HOST,
            "port": MILVUS_PORT,
            "user": MILVUS_USERNAME,
            "password": MILVUS_PASSWORD,
        },
        collection_name=MILVUS_COLLECTION,
        metadata_field="metadata",
        text_field="page_content",
        auto_id=True,
        drop_old=True,
    )

    print(f"Uploading documents to collection {MILVUS_COLLECTION}")

    db.add_documents(splits)

    print("Finished!")
