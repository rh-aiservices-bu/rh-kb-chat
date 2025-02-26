# Document Ingestion Data Science Pipeline

This data science pipeline automates the process of ingesting documentation from collections and storing them in a Milvus vector database with embeddings for retrieval.

## Overview

The pipeline processes documentation collections, generates embeddings, and stores them in Milvus to be used in retrieval systems. It handles various operations (create, update, delete) based on directives specified in the collection configuration.

## Components

### Main Pipeline (`doc_ingestion_pipeline.py`)
- Defines a Kubeflow Pipeline for document ingestion
- Connects to a Data Science Pipelines Application server
- Executes the document ingestion task with necessary secrets

### Document Processor (`doc_processing_docling_server.py`)
- KFP component that handles the actual document ingestion process
- Loads collections from either a local path or Git repository
- Processes documents according to their storage directives
- Manages connections to Milvus and embedding services
- Provides detailed progress logging

## Requirements

### Custom Image
The pipeline requires a custom image built from the [Containerfile](./Containerfile) in this directory. The image is published at: `quay.io/rh-aiservices-bu/rh-kb-doc-ingestion:1.0`

### Required Secret
The pipeline requires a Kubernetes secret named `doc-ingestion` containing the following keys:
- `EMBEDDINGS_API_KEY`: API key for embeddings service
- `EMBEDDINGS_API_URL`: URL for embeddings service
- `EMBEDDINGS_MODEL_NAME`: Model name for embeddings
- `MILVUS_URI`: URI for Milvus database
- `MILVUS_USERNAME`: Milvus username
- `MILVUS_PASSWORD`: Milvus password
- `MILVUS_DB`: Milvus database name
- `MILVUS_BATCH_SIZE`: Batch size for Milvus operations
- `CHUNK_SIZE`: Size of text chunks for processing
- `CHUNK_OVERLAP`: Overlap between chunks
- `DOCLING_API_URL`: URL for Docling API
- `DOCLING_API_KEY`: API key for Docling service
- `COLLECTIONS_PATH`: Path to collections (optional)
- `COLLECTIONS_GIT_REPO_NAME`: Git repo name (optional)
- `COLLECTIONS_GIT_REPO_PATH`: Git repo path (optional)
- `COLLECTIONS_GIT_REPO_BRANCH`: Git repo branch (optional)

## Usage

This pipeline is typically triggered by the Tekton pipeline when changes are detected in the collections directory. It can also be run manually through the Data Science Pipelines UI or API.

The pipeline will:
1. Load collections from the specified source
2. Process each collection according to its directive (create, update, delete)
3. Split documents into chunks with configurable size and overlap
4. Generate embeddings for the content chunks
5. Store the indexed content in Milvus
6. Log detailed progress information

## Supported Operations

- `create_or_keep`: Creates a new collection if it doesn't exist, skips if it does
- `update`: Creates or replaces a collection unconditionally
- `delete`: Removes a collection if it exists