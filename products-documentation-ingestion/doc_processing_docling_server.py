import kfp
import kfp.dsl as dsl
from kfp.dsl import (
    component
)

@component(target_image='quay.io/rh-aiservices-bu/rh-kb-doc-ingestion:1.0')
def doc_ingest():
    """
    Start ingesting the docs
    """

    import os

    from dotenv import load_dotenv

    import collections_loader as cl
    import milvus_handler
    import traceback

    load_dotenv()

    collections_path = os.getenv("COLLECTIONS_PATH")
    collections_git_repo_name = os.getenv("COLLECTIONS_GIT_REPO_NAME")
    collections_git_repo_path = os.getenv("COLLECTIONS_GIT_REPO_PATH")
    collections_git_repo_branch = os.getenv("COLLECTIONS_GIT_REPO_BRANCH")


    # Load all JSON files into the collections object
    collections = []
    collection_loader = cl.CollectionLoader()
    if collections_path is not None:
        collection_loader.fetch_collections_from_path(collections, collections_path)
    if collections_git_repo_name is not None:
        collections = collection_loader.fetch_collections_from_git(collections, collections_git_repo_name, collections_git_repo_path, collections_git_repo_branch)


    milvus_endpoint = {}
    embeddings_endpoint = {}

    milvus_uri = os.getenv("MILVUS_URI")
    milvus_username = os.getenv("MILVUS_USERNAME")
    milvus_password = os.getenv("MILVUS_PASSWORD")
    milvus_db = os.getenv("MILVUS_DB")
    milvus_batch_size = int(os.getenv("MILVUS_BATCH_SIZE"))
    chunk_size = int(os.getenv("CHUNK_SIZE"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP"))
    embeddings_api_url = os.getenv("EMBEDDINGS_API_URL")
    embeddings_api_key = os.getenv("EMBEDDINGS_API_KEY")
    embeddings_model_name = os.getenv("EMBEDDINGS_MODEL_NAME")

    milvus_handler = milvus_handler.MilvusHandler(
        milvus_uri,
        milvus_username,
        milvus_password,
        milvus_db,
        milvus_batch_size,
        embeddings_api_url,
        embeddings_api_key,
        embeddings_model_name
    )

    # At the start of processing, log total counts
    print(f"\n==== STARTING DOCUMENT PROCESSING ====")
    print(f"Found {len(collections)} collections to process")
    total_versions = sum(len(collection.versions) for collection in collections)
    print(f"Total document versions to process: {total_versions}\n")

    # Counter for progress tracking
    processed_count = 0

    for collection in collections:
        print(f"\n📚 COLLECTION: {collection.collection_full_name}")
        print(f"Base name: {collection.collection_base_name}")
        print(f"Contains {len(collection.versions)} version(s)")
        
        for version in collection.versions:
            processed_count += 1
            progress = (processed_count / total_versions) * 100
            
            print('\n' + '=' * 80)
            print(f"⏳ PROCESSING [{processed_count}/{total_versions}] ({progress:.1f}%)")
            print(f"Collection: \"{collection.collection_full_name}\"")
            print(f"Version: \"{version.version_number}\"")
            print(f"Directive: \"{version.store_directive}\"")
            
            collection_name = (
                f"{collection.collection_base_name}_{version.version_number}"
                .replace("-", "_")
                .replace(".", "_")
            )
            
            # If you have URLs to process, show them clearly
            if hasattr(version, 'urls') and version.urls:
                print("\nProcessing URLs:")
                for idx, url in enumerate(version.urls, 1):
                    print(f"  {idx}. {url}")
            
            if (version.store_directive == 'create_or_keep'):
                if (milvus_handler.collection_check(collection_name) is None):
                    print("\n▶️ Collection not present, creating it...")
                    try:
                        print(f'▶️ Creating "{collection.collection_full_name}" at version {version.version_number}')
                        milvus_handler.ingest_documentation(collection, version, chunk_size, chunk_overlap)
                        print("✅ Successfully created collection")
                    except Exception as e:
                        print(f'❌ Error processing "{collection.collection_full_name}" at version {version.version_number}')
                        print(f'❌ {e}')
                        traceback.print_exc()
                else:
                    print("\n⏭️ Collection already present, skipping")
            elif (version.store_directive == 'update'):
                print("\n🔄 No check needed, creating/replacing the collection anyway...")
                try:
                    print(f'🔄 Updating "{collection.collection_full_name}" at version {version.version_number}')
                    milvus_handler.ingest_documentation(collection, version, chunk_size, chunk_overlap)
                    print("✅ Successfully updated collection")
                except Exception as e:
                    print(f'❌ Error processing "{collection.collection_full_name}" at version {version.version_number}')
                    print(f'❌ {e}')
                    traceback.print_exc()
            elif (version.store_directive == 'delete'):
                if (milvus_handler.collection_check(collection_name) is None):
                    print("\n⏭️ No collection present already, skipping")
                else:
                    print("\n🗑️ Let's delete it")
                    milvus_handler.collection_delete(collection_name)
                    print("✅ Successfully deleted collection")
            
            print(f"Completed processing [{processed_count}/{total_versions}]")

    print("\n==== DOCUMENT PROCESSING COMPLETE ====")
    print(f"Processed {processed_count} document versions across {len(collections)} collections")
    print("Done!")