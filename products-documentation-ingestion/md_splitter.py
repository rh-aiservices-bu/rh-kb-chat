from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


def split(md_docs, product, product_full_name, version=None, language=None, url=None, chunk_size=768, chunk_overlap=128):
    # Generates splits from a list of Markdown documents

    # Markdown splitter config
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on, strip_headers=True
    )

    # Markdown split
    new_splits = []
    for doc in md_docs:
        md_header_splits = markdown_splitter.split_text(doc.page_content)
        for split in md_header_splits:
            split.metadata = split.metadata | doc.metadata
            split.metadata["product"] = product
            split.metadata["product_full_name"] = product_full_name
            if version is not None:
                split.metadata["version"] = version
            if language is not None:
                split.metadata["language"] = language
            if url is not None:
                split.metadata["url"] = url
            
        new_splits.extend(md_header_splits)

    # Char-level splitter config
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    # Char-level split in case the Markdown split is too large
    splits = text_splitter.split_documents(new_splits)

    # Add content headers to each split
    for split in splits:
        # 'search_document:' part added to guide nomic in the embeddings
        content_header = f"search_document: Section: {split.metadata['title']}"
        for header_name in ["Header 1", "Header 2", "Header 3"]:
            if header_name in split.metadata:
                content_header += f" / {split.metadata[header_name]}"
        content_header += "\n\nContent:\n"
        split.page_content = content_header + split.page_content

    return splits
