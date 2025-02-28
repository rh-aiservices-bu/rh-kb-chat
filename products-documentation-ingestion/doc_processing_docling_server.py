import requests
from dotenv import load_dotenv
import os
import md_splitter
from langchain_core.documents import Document

load_dotenv()


def docling_processing(url):
    # Process the given URL using the Docling API
    api_address = os.getenv("DOCLING_API_URL")
    api_key = os.getenv("DOCLING_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    print(f"Processing: {url}")
    payload = {
        "http_sources": [{"url": url}],
        "options": {"to_formats": ["md"], "image_export_mode": "placeholder"},
    }
    response = requests.post(
        f"{api_address}/v1alpha/convert/source", json=payload, headers=headers
    )
    md_content = response.json()["document"]["md_content"]
    return md_content


def generate_splits(urls, product, product_full_name, chunk_size, chunk_overlap):
    # Generate splits from the given URLs
    all_splits = []
    for url in urls:
        print(f"Processing: {url}")
        md_content = docling_processing(url)
        # Get the title of the document from the last part of the URL
        title = url.split("/")[-1]
        # Add metadata
        metadata = {"source": url, "title": title}
        md_doc = [Document(page_content=md_content, metadata=metadata)]
        splits = md_splitter.split(
            md_doc,
            product,
            product_full_name,
            url=url,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_splits.extend(splits)
    print(f"Generated {len(all_splits)} splits.")

    return all_splits