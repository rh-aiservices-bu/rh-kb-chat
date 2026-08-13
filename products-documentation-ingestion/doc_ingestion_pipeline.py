# kfp imports
import kfp
import kfp.dsl as dsl
from kfp.dsl import (
    component
)
from kfp import kubernetes

# Misc imports
import os

# Component imports
from documentation_ingestion import doc_ingest

######### Pipeline definition #########

ingestion_secret_name = 'doc-ingestion'

# Create pipeline
@dsl.pipeline(
  name='doc-ingestion-pipeline',
  description='Ingest ALL the documents📚💪'
)
def doc_ingestion_pipeline():
    ### 🐶 Document ingestion
    doc_ingestion_task = doc_ingest()
    kubernetes.use_secret_as_env(
        doc_ingestion_task,
        secret_name=ingestion_secret_name,
        secret_key_to_env={
            'EMBEDDINGS_API_KEY': 'EMBEDDINGS_API_KEY',
            'EMBEDDINGS_API_URL': 'EMBEDDINGS_API_URL',
            'MILVUS_URI': 'MILVUS_URI',
            'MILVUS_PASSWORD': 'MILVUS_PASSWORD',
            'MILVUS_USERNAME': 'MILVUS_USERNAME',
            'MILVUS_DB': 'MILVUS_DB',
            'MILVUS_BATCH_SIZE': 'MILVUS_BATCH_SIZE',
            'CHUNK_SIZE': 'CHUNK_SIZE',
            'CHUNK_OVERLAP': 'CHUNK_OVERLAP',
            'EMBEDDINGS_API_URL': 'EMBEDDINGS_API_URL',
            'EMBEDDINGS_API_KEY': 'EMBEDDINGS_API_KEY',
            'EMBEDDINGS_MODEL_NAME': 'EMBEDDINGS_MODEL_NAME',
            'DOCLING_API_URL': 'DOCLING_API_URL',
            'DOCLING_API_KEY': 'DOCLING_API_KEY',
            'COLLECTIONS_PATH': 'COLLECTIONS_PATH',
            'COLLECTIONS_GIT_REPO_NAME': 'COLLECTIONS_GIT_REPO_NAME',
            'COLLECTIONS_GIT_REPO_PATH': 'COLLECTIONS_GIT_REPO_PATH',
            'COLLECTIONS_GIT_REPO_BRANCH': 'COLLECTIONS_GIT_REPO_BRANCH'
        },
    )
    
if __name__ == '__main__':
        
    namespace_file_path =\
        '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    with open(namespace_file_path, 'r') as namespace_file:
        namespace = namespace_file.read()

    kubeflow_endpoint =\
        f'https://ds-pipeline-dspa.{namespace}.svc:8443'

    sa_token_file_path = '/var/run/secrets/kubernetes.io/serviceaccount/token'
    with open(sa_token_file_path, 'r') as token_file:
        bearer_token = token_file.read()

    ssl_ca_cert =\
        '/var/run/secrets/kubernetes.io/serviceaccount/service-ca.crt'

    print(f'Connecting to Data Science Pipelines: {kubeflow_endpoint}')
    client = kfp.Client(
        host=kubeflow_endpoint,
        existing_token=bearer_token,
        ssl_ca_cert=ssl_ca_cert
    )

    client.create_run_from_pipeline_func(
        doc_ingestion_pipeline,
        experiment_name="doc-ingestion",
        enable_caching=True
    )
