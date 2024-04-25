from bs4 import BeautifulSoup
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_community.document_transformers import Html2TextTransformer
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from redhat_documentation import RedHatDocumentationLoader


def get_pages(product, version, language):
    """Get the list of pages from the Red Hat product documentation."""

    # Load the Red Hat documentation page
    url = [
        "https://access.redhat.com/documentation/"
        + language
        + "/"
        + product
        + "/"
        + version
    ]
    loader = WebBaseLoader(url)
    soup = loader.scrape()

    # Select only the element titles that contain the links to the documentation pages
    filtered_elements = soup.find_all("h3", class_="list-result-title heading-inline")
    new_soup = BeautifulSoup("", "lxml")
    for element in filtered_elements:
        new_soup.append(element)
    for match in new_soup.findAll("h3"):
        match.unwrap()

    # Extract all the links
    links = []
    for match in new_soup.findAll("a"):
        links.append(match.get("href"))
    links = [
        url for url in links if url.startswith("/documentation")
    ]  # Filter out unwanted links
    pages = [
        link.replace("/html/", "/html-single/") for link in links if "/html/" in link
    ]  # We want single pages html

    return pages


def split_document(product, version, language, page, product_full_name):
    """Split a Red Hat documentation page into smaller sections."""

    # Load, parse, and transform to Markdown
    document_url = ["https://access.redhat.com" + page]
    print(f"Processing: {document_url}")
    loader = RedHatDocumentationLoader(document_url)
    docs = loader.load()
    html2text = Html2TextTransformer()
    md_docs = html2text.transform_documents(docs)

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
            split.metadata["version"] = version
            split.metadata["language"] = language
            split.metadata["product_full_name"] = product_full_name
        new_splits.extend(md_header_splits)

    # Char-level splitter config
    chunk_size = 2048
    chunk_overlap = 256
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    # Char-level split
    splits = text_splitter.split_documents(new_splits)

    for split in splits:
        content_header = f"Section: {split.metadata['title']}"
        for header_name in ["Header 1", "Header 2", "Header 3"]:
            if header_name in split.metadata:
                content_header += f" / {split.metadata[header_name]}"
        content_header += "\n\nContent:\n"
        split.page_content = content_header + split.page_content

    return splits


def generate_splits(product, product_full_name, version, language):
    """Generate the splits for a Red Hat documentation product."""

    # Find all the pages.
    pages = get_pages(product, version, language)
    print(f"Found {len(pages)} pages:")
    print(pages)

    # Generate the splits.
    print("Generating splits...")
    all_splits = []
    for page in pages:
        splits = split_document(product, version, language, page, product_full_name)
        all_splits.extend(splits)
    print(f"Generated {len(all_splits)} splits.")

    return all_splits
