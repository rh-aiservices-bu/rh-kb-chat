from typing import List

from bs4 import BeautifulSoup
from langchain_community.document_transformers import Html2TextTransformer
from langchain_core.documents import Document
import requests

import md_splitter


def fetch_soup(url):
    """Fetch public documentation without WebBaseLoader's blocked headers."""
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    if soup.title and soup.title.get_text(strip=True) == "Access Denied":
        raise RuntimeError(f"Red Hat Documentation denied access to {url}")
    return soup


class RedHatDocumentationLoader:
    """Load `Red Hat Documentation` single-html webpages."""

    def __init__(self, web_paths):
        self.web_path = web_paths[0]

    def load(self) -> List[Document]:
        """Load webpages as Documents."""
        soup = fetch_soup(self.web_path)
        title_element = soup.select_one("h1.title") or soup.select_one("h1")
        if title_element is None:
            raise RuntimeError(f"No document title found at {self.web_path}")
        title = title_element.get_text(" ", strip=True)

        # Get main content
        book = soup.select_one(".book")
        if book:
            soup = book
        else:
            article = soup.select_one(".article")
            if article:
                soup = article
            else:
                soup = None

        if soup is not None:
            # Remove unwanted sections
            unwanted_classes = [
                "producttitle",
                "subtitle",
                "abstract",
                "legalnotice",
                "calloutlist",
                "callout",
            ]
            for unwanted_class in unwanted_classes:
                for div in soup.find_all("div", {"class": unwanted_class}):
                    div.decompose()
                for span in soup.find_all("span", {"class": unwanted_class}):
                    span.decompose()
                for header in soup.find_all("h2", {"class": unwanted_class}):
                    header.decompose()
            for hr in soup.find_all("hr"):
                hr.decompose()

            # Find and delete anchor tag with content "Legal Notice"
            for anchor in soup.find_all("a"):
                if anchor.text == "Legal Notice":
                    anchor.decompose()

            # Unwrap unwanted tags
            unwrap_tags = ["div", "span", "strong", "section"]
            for tag in unwrap_tags:
                for match in soup.findAll(tag):
                    match.unwrap()

            # Transform description titles
            for dt in soup.find_all("dt"):
                if dt.string:
                    dt.string.replace_with(f"-> {dt.string}")

            # Transform code blocks
            for code in soup.find_all("pre", {"class": "programlisting"}):
                try:
                    content = code.text
                    code.clear()
                    if "language-yaml" in code["class"]:
                        code.string = f"```yaml\n{content}\n```"
                    elif "language-json" in code["class"]:
                        code.string = f"```json\n{content}\n```"
                    elif "language-bash" in code["class"]:
                        code.string = f"```bash\n{content}\n```"
                    elif "language-python" in code["class"]:
                        code.string = f"```python\n{content}\n```"
                    elif "language-none" in code["class"]:
                        code.string = f"```\n{content}\n```"
                    else:
                        code.string = f"```\n{content}\n```"
                except Exception as e:
                    print(f"Error processing code block: {e}")
            for code in soup.find_all("pre", {"class": "screen"}):
                try:
                    content = code.text
                    code.clear()
                    code.string = f"```console\n{content}\n```"
                except Exception as e:
                    print(f"Error processing code block: {e}")

            # Remove all attributes
            for tag in soup():
                tag.attrs.clear()

            text = str(soup)  # Convert to string
            text = text.replace("\xa0", " ")  # Replace non-breaking space

        else:
            text = ""

        # Add metadata
        metadata = {"source": self.web_path, "title": title}

        return [Document(page_content=text, metadata=metadata)]


def get_pages(product, version, language):
    """Get the list of pages from the Red Hat product documentation."""

    # Load the Red Hat documentation page
    if language != "en-US":
        raise ValueError(f"Unsupported Red Hat documentation language: {language}")
    url = f"https://docs.redhat.com/en/documentation/{product}/{version}"
    soup = fetch_soup(url)

    # Select only the element titles that contain the links to the documentation pages
    filtered_elements = soup.find_all("h3", attrs={"slot": "headline"})
    new_soup = BeautifulSoup("", "lxml")
    for element in filtered_elements:
        new_soup.append(element)
    for match in new_soup.findAll("h3"):
        match.unwrap()

    # Extract all the links
    links = []
    for match in new_soup.findAll("a"):
        href = match.get("href")
        if href:
            links.append(href)
    links = [
        url for url in links
        if (url.startswith("https://docs.redhat.com/en/documentation") or
            url.startswith("/en/documentation") or
            url.startswith("/en-US/documentation"))
    ]  # Filter out unwanted links
    pages = [
        link.replace("/html/", "/html-single/") for link in links if "/html/" in link
    ]  # We want single pages html

    # Preserve order while removing duplicate links.
    pages = list(dict.fromkeys(pages))
    if not pages:
        raise RuntimeError(f"No documentation page links found at {url}")

    return pages


def split_document(product, version, language, page, product_full_name, chunk_size, chunk_overlap):
    """Split a Red Hat documentation page into smaller sections."""

    # Load, parse, and transform to Markdown
    document_url = [page if page.startswith("http") else "https://docs.redhat.com" + page]
    print(f"Processing: {document_url}")
    loader = RedHatDocumentationLoader(document_url)
    docs = loader.load()
    html2text = Html2TextTransformer()
    md_docs = html2text.transform_documents(docs)

    splits = md_splitter.split(md_docs, product, product_full_name, version=version, language=language, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    return splits


def generate_splits(product, product_full_name, version, language, chunk_size, chunk_overlap):
    """Generate the splits for a Red Hat documentation product."""

    # Find all the pages.
    pages = get_pages(product, version, language)
    print(f"Found {len(pages)} pages:")
    print(pages)

    # Generate the splits.
    print("Generating splits for Red Hat doc...")
    all_splits = []
    for page in pages:
        try:
            splits = split_document(
                product,
                version,
                language,
                page,
                product_full_name,
                chunk_size,
                chunk_overlap,
            )
        except requests.HTTPError as exc:
            # Product landing pages occasionally retain links to guides that
            # have been removed. Do not discard every valid guide in the
            # product/version because of one stale catalog entry.
            if exc.response is not None and exc.response.status_code == 404:
                print(f"WARNING: Documentation page not found, skipping: {page}")
                continue
            raise
        all_splits.extend(splits)
    print(f"Generated {len(all_splits)} splits.")

    return all_splits
