from classes import Collection, Source, VersionInfo
import os
import requests
import json

class CollectionLoader:
    """Class to load collections from JSON files or from a git repository"""
    
    def load_collection_from_json(self, data: str) -> Collection:
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


    def fetch_collections_from_git(self, collections, git_repo_name, git_repo_path, git_branch="main"):
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
                collection = self.load_collection_from_json(data)
                collections.append(collection)

        return collections

    def fetch_collections_from_path(self, collections, path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith(".json"):
                    with open(os.path.join(root, file), "r") as f:
                        data = json.load(f)
                        collection = self.load_collection_from_json(data)
                        collections.append(collection)

        return collections