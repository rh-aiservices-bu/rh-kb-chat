class Source:
    def __init__(self, ingestion_type, language=None, urls=None):
        self.ingestion_type: str = ingestion_type
        self.language: str | None = language
        self.urls: list[str] | None = urls

    def __repr__(self):
        return f"Source(ingestion_type={self.ingestion_type}, language={self.language}, urls={self.urls})"


class VersionInfo:
    def __init__(self, version_number, store_directive, sources):
        self.version_number: str = version_number
        self.store_directive: str = store_directive
        self.sources: list[Source] = sources

    def __repr__(self):
        return f"VersionInfo(version_number={self.version_number}, store_directive={self.store_directive}, sources={self.sources}"


class Collection:
    def __init__(self, collection_base_name, collection_full_name, versions, common_sources=None):
        self.collection_base_name: str = collection_base_name
        self.collection_full_name: str = collection_full_name
        self.versions: list[VersionInfo] = versions
        self.common_sources: list[Source] | None = common_sources

    def __repr__(self):
        return f"ProductInfo(collection_base_name={self.collection_base_name}, collection_full_name={self.collection_full_name}, versions={self.versions}, common_sources={self.common_sources})"