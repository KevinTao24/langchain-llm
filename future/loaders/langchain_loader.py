import logging
from typing import List

from bs4 import BeautifulSoup, SoupStrainer
from langchain.utils.html import PREFIXES_TO_IGNORE_REGEX, SUFFIXES_TO_IGNORE_REGEX
from langchain_community.document_loaders import RecursiveUrlLoader, SitemapLoader

from future.parsers.langchain_parser import langchain_docs_parser, langsmith_docs_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LANGCHAIN_DOCS_URL = "https://python.langchain.com/"
LANGSMITH_DOCS_URL = "https://docs.smith.langchain.com/"


class LangchainDocsLoader:
    def __init__(
        self,
        url: str,
        filter_urls: List[str] | None = None,
    ):
        self.url = url
        self.filter_urls = filter_urls

    def _metadata_extractor(meta: dict, soup: BeautifulSoup) -> dict:
        title = soup.find("title")
        description = soup.find("meta", attrs={"name": "description"})
        html = soup.find("html")
        return {
            "source": meta["loc"],
            "title": title.get_text() if title else "",
            "description": description.get("content", "") if description else "",
            "language": html.get("lang", "") if html else "",
            **meta,
        }

    def load_langchain_docs(self):
        return SitemapLoader(
            self.url,
            filter_urls=self.filter_urls,
            parsing_function=langchain_docs_parser,
            default_parser="lxml",
            bs_kwargs={
                "parse_only": SoupStrainer(
                    name=("article", "title", "html", "lang", "content")
                ),
            },
            meta_function=self._metadata_extractor,
        ).load()


class LangsmithDocsLoader:
    def __init__(self, url: str = LANGSMITH_DOCS_URL):
        self.url = url

    def load_langsmith_docs(self):
        return RecursiveUrlLoader(
            url=self.url,
            max_depth=8,
            extractor=langsmith_docs_parser,
            prevent_outside=True,
            use_async=True,
            timeout=600,
            # Drop trailing / to avoid duplicate pages.
            link_regex=(
                f"href=[\"']{PREFIXES_TO_IGNORE_REGEX}((?:{SUFFIXES_TO_IGNORE_REGEX}.)*?)"
                r"(?:[\#'\"]|\/[\#'\"])"
            ),
            check_response_status=True,
        ).load()


if __name__ == "__main__":
    langchain_loader = LangchainDocsLoader()
    langchain_docs = langchain_loader.load_langchain_docs()

    langsmith_loader = LangsmithDocsLoader()
    langsmith_docs = langsmith_loader.load_langsmith_docs()
