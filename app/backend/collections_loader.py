import json
import os

import requests
from pymilvus import MilvusClient

from classes import Collection, Source, VersionInfo


class CollectionsLoader:
    """Class to load collections from JSON files or from a git repository"""
    def __init__(self, collection_config, vectorstore_config, logger):
        self.collections = []
        self.collections_path = collection_config.get("local_path")
        self.collections_git_repo_name = collection_config.get("git_repo_name")
        self.collections_git_repo_path = collection_config.get("git_repo_path")
        self.collections_git_repo_branch = collection_config.get("git_repo_branch")
        self.vectorstore_config = vectorstore_config
        self._logger = logger
    
    def _load_collection_from_json(self, data: str) -> Collection:
        # Parse common_sources
        common_sources = [
            Source(
                ingestion_type=source.get("ingestion_type"),
                language=source.get("language"),
                urls=source.get("urls")
            ) for source in data.get("common_sources", [])
        ]

        # Parse versions
        versions = [
            VersionInfo(
                version_number=version.get("version_number"),
                store_directive=version.get("directive", version.get("store_directive")),  # Handle possible key mismatch
                sources=[
                    Source(
                        ingestion_type=src.get("ingestion_type"),
                        language=src.get("language"),
                        urls=src.get("urls")
                    ) for src in version.get("sources", [])
                ]
            ) for version in data.get("versions", [])
        ]

        # Create the Collection object
        collection = Collection(
            collection_base_name=data.get("collection_base_name"),
            collection_full_name=data.get("collection_full_name"),
            versions=versions,
            common_sources=common_sources
        )

        return collection


    def _fetch_collections_from_git(self, collections, git_repo_name, git_repo_path, git_branch="main"):
        repo_url = f"https://api.github.com/repos/{git_repo_name}/contents/{git_repo_path}?ref={git_branch}"
        response = requests.get(repo_url)
        response.raise_for_status()
        files = response.json()

        for file in files:
            if file["name"].endswith(".json"):
                file_url = file["download_url"]
                file_response = requests.get(file_url)
                file_response.raise_for_status()
                data = file_response.json()
                collection = self._load_collection_from_json(data)
                collections.append(collection)

        return collections

    def _fetch_collections_from_path(self, collections, path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), "r") as f:
                        data = json.load(f)
                        collection = self._load_collection_from_json(data)
                        collections.append(collection)
        return collections
    
    def _filter_collections(self):
        """Filter collections based on them being available in Milvus"""
        milvus_uri = self.vectorstore_config.get('uri', 'localhost')
        milvus_user = self.vectorstore_config.get('user', '')
        milvus_password = self.vectorstore_config.get('password', '')
        milvus_db = self.vectorstore_config.get('db_name', 'default')
        milvus_client = MilvusClient(
                    uri=milvus_uri,
                    user=milvus_user,
                    password=milvus_password,
                    db_name=milvus_db
                )
        self._logger.info(f'Connected to Milvus at {milvus_uri}')

        # Load collections from Milvus
        milvus_collections = milvus_client.list_collections()

        # Filter collections
        new_collections = []
        for collection in self.collections:
            new_versions = []
            for version in collection.versions:
                milvus_collection_name = (
                    f"{collection.collection_base_name}_{version.version_number}"
                    .replace("-", "_")
                    .replace(".", "_")
                )
                # Replace needed because Milvus collection names cannot contain hyphens or periods

                if milvus_collection_name in milvus_collections:
                    new_versions.append(version)
            if len(new_versions) > 0:
                collection.versions = new_versions
                new_collections.append(collection)
        self.collections = new_collections
    
    def load_collections(self):
        if self.collections_path is not None and self.collections_path != "":
            self._logger.info(f"Loading collections from path: {self.collections_path}")
            self._fetch_collections_from_path(self.collections, self.collections_path)
        if self.collections_git_repo_name is not None and self.collections_git_repo_path != "":
            self._logger.info(f"Loading collections from git: {self.collections_git_repo_name}/{self.collections_git_repo_path} in branch {self.collections_git_repo_branch}")
            self.collections = self._fetch_collections_from_git(
                self.collections,
                self.collections_git_repo_name,
                self.collections_git_repo_path,
                self.collections_git_repo_branch
            )
        self._filter_collections()

        return self.collections