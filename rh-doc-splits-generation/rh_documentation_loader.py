from typing import List

from bs4 import BeautifulSoup
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_core.documents import Document


class RedHatDocumentationLoader(WebBaseLoader):
    """Load `Red Hat Documentation` single-html webpages."""

    def load(self) -> List[Document]:
        """Load webpages as Documents."""
        soup = self.scrape()
        title = soup.select_one("h1", {"class": "title"}).text  # Get title

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
