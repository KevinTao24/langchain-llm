from typing import Any, Dict, List, Optional

import requests
from langchain_core.embeddings import Embeddings
from langchain_core.pydantic_v1 import BaseModel, SecretStr, root_validator
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env

ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/embeddings"


class ZhipuTextEmbedding(BaseModel, Embeddings):
    """Zhipu Text Embedding models."""

    session: Any  #: :meta private:
    model_name: str = "embedding-2"
    zhipu_api_key: Optional[SecretStr] = None

    @root_validator(allow_reuse=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that auth token exists in environment."""
        try:
            zhipu_api_key = convert_to_secret_str(
                get_from_dict_or_env(values, "zhipu_api_key", "ZHIPU_API_KEY")
            )
        except ValueError as original_exc:
            raise original_exc

        session = requests.Session()
        session.headers.update(
            {
                "Authorization": f"Bearer {zhipu_api_key.get_secret_value()}",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-type": "application/json",
            }
        )
        values["session"] = session
        return values

    def embed_documents(self, texts: List[str]) -> Optional[List[List[float]]]:  # type: ignore[override]
        """Public method to get embeddings for a list of documents.

        Args:
            texts: The list of texts to embed.

        Returns:
            A list of embeddings, one for each text, or None if an error occurs.
        """
        return self._embed(texts)

    def embed_query(self, text: str) -> Optional[List[float]]:  # type: ignore[override]
        """Public method to get embedding for a single query text.

        Args:
            text: The text to embed.

        Returns:
            Embeddings for the text, or None if an error occurs.
        """
        result = self._embed([text])
        return result[0] if result is not None else None

    def _embed(self, texts: List[str]) -> Optional[List[List[float]]]:
        """Internal method to call Zhipu Embedding API and return embeddings.

        Args:
            texts: A list of texts to embed.

        Returns:
            A list of list of floats representing the embeddings, or None if an
            error occurs.
        """
        try:
            results = []
            for text in texts:
                response = self.session.post(
                    ZHIPU_API_URL, json={"input": text, "model": self.model_name}
                )
                # Check if the response status code indicates success
                if response.status_code == 200:
                    resp = response.json()
                    embeddings = resp.get("data", [])[0]
                    results.append(embeddings.get("embedding", []))
                else:
                    # Log error or handle unsuccessful response appropriately
                    print(  # noqa: T201
                        f"""Error: Received status code {response.status_code} from 
                        embedding API"""
                    )
                    return None
            return results
        except Exception as e:
            # Log the exception or handle it as needed
            print(
                f"Exception occurred while trying to get embeddings: {str(e)}"
            )  # noqa: T201
            return None


if __name__ == "__main__":
    documents = ["智谱大模型", "智谱向量模型"]
    embedding = ZhipuTextEmbedding()
    output = embedding.embed_documents(documents)
    print(output)
