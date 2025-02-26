import os

from langchain_milvus import Milvus
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from pymilvus import MilvusClient
from dotenv import load_dotenv

import doc_processing_rh_doc as dp_rh
import doc_processing_docling_server as dp_ds

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

load_dotenv()

class MilvusHandler:
    def __init__(
        self,
        milvus_uri,
        milvus_username,
        milvus_password,
        milvus_db="default",
        milvus_batch_size=32,
        embeddings_api_url="",
        embeddings_api_key="",
        embeddings_model_name=""
    ):
        self.milvus_uri = milvus_uri
        self.milvus_username = milvus_username
        self.milvus_password = milvus_password
        self.milvus_db = milvus_db
        self.milvus_batch_size = milvus_batch_size
        self.embeddings_api_url = embeddings_api_url
        self.embeddings_api_key = embeddings_api_key
        self.embeddings_model_name = embeddings_model_name
        self.client = MilvusClient(
            uri=self.milvus_uri,
            user=self.milvus_username,
            password=self.milvus_password,
            db_name=self.milvus_db
        )
        self.embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_url=self.embeddings_api_url,
            api_key=self.embeddings_api_key,
            model_name=self.embeddings_model_name
        )
        # check_embedding_ctx_length=False,

    def collection_check(self, collection_name):
        collections = self.client.list_collections()
        if collection_name in collections:
            return self.client.describe_collection(collection_name)
        else:
            return None

    def collection_delete(self, collection_name):
        collections = self.client.list_collections()
        if collection_name in collections:
            try:
                self.client.drop_collection(collection_name)
            except Exception as e:
                print(f'Error dropping "{collection_name}"')
                print(f"{e}")


    def per_type_ingestion(self, splits, source, collection, version, chunk_size, chunk_overlap):
        if source.ingestion_type == "docling_server":
                splits += dp_ds.generate_splits(
                        source.urls,
                        product=collection.collection_base_name,
                        product_full_name=collection.collection_full_name,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
        elif source.ingestion_type == "redhat_doc":
            splits += dp_rh.generate_splits(
                collection.collection_base_name,
                collection.collection_full_name,
                version.version_number,
                source.language,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )


    def ingest_documentation(self, collection, version, chunk_size=768, chunk_overlap=128, drop_old=True, batch_size=600):
        """Ingest documentation into Milvus"""

        collection_name = (
            f"{collection.collection_base_name}_{version.version_number}".replace(
                "-", "_"
            ).replace(".", "_")
        )
        # Replace needed because Milvus collection names cannot contain hyphens or periods

        splits = []

        # if the collection has common sources, add them to the splits
        if collection.common_sources:
            for source in collection.common_sources:
                self.per_type_ingestion(splits, source, collection, version, chunk_size, chunk_overlap)

        # add the splits from selected version
        for source in version.sources:
            self.per_type_ingestion(splits, source, collection, version, chunk_size, chunk_overlap)

        vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args={
                "uri": self.milvus_uri,
                "user": self.milvus_username,
                "password": self.milvus_password,
                "db_name": self.milvus_db,
            },
            collection_name=collection_name,
            enable_dynamic_field=True,
            text_field="page_content",
            auto_id=True,
            drop_old=drop_old,
        )

        print(
            f"Calculating embeddings and uploading documents to collection {collection_name}"
        )

        # Process in batches of 600
        total_splits = len(splits)
        for i in range(0, total_splits, batch_size):
            end_idx = min(i + batch_size, total_splits)
            current_batch = splits[i:end_idx]
            print(f"Processing batch {i//batch_size + 1}/{(total_splits + batch_size - 1)//batch_size}: documents {i} to {end_idx-1}")
            vector_store.add_documents(current_batch, batch_size=self.milvus_batch_size)

        print("Ingestion finished!")

    def similarity_search_with_score(self, collection, version, query, top_k=4):
        collection_name = (
            f"{collection.collection_base_name}_{version.version_number}".replace(
                "-", "_"
            ).replace(".", "_")
        )

        vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args={
                "uri": self.milvus_uri,
                "user": self.milvus_username,
                "password": self.milvus_password,
                "db_name": self.milvus_db,
            },
            collection_name=collection_name,
            enable_dynamic_field=True,
            text_field="page_content",
            auto_id=True,
            drop_old=False,
        )

        results = vector_store.similarity_search_with_score(query, k=top_k)

        return results
