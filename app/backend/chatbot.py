import base64
import binascii
import os
import re

from openai import APIError, AsyncOpenAI

from litellm_embeddings import LiteLLMEmbeddings
from milvus_retriever_with_score_threshold import MilvusRetrieverWithScoreThreshold


DEFAULT_SYSTEM_TEMPLATE = """You are a helpful, respectful, and honest assistant answering questions about Red Hat products. Answer in {language}. Use only the supplied references when references are available. If the references do not contain enough information, say that you do not know based on the available references. You may analyze an attached image when the selected model supports vision. Do not invent facts or sources. Do not translate code, commands, configuration keys, product names, URLs, or quoted text."""
DEFAULT_TRANSLATE_TEMPLATE = """Translate the user's text to English. Return only the translation, with no explanation or label. Preserve code, commands, configuration keys, product names, URLs, and quoted literals exactly. If the text is already English, return it unchanged."""
IMAGE_DATA_URL = re.compile(r"^data:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=\r\n]+)$")
MAX_IMAGE_BYTES = 5 * 1024 * 1024


class Chatbot:
    """Multimodal chat-completions client backed by Milvus text retrieval."""

    def __init__(self, config, logger):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        self.logger = logger
        self.config = config
        self.llms_config = config.get("llms", [])
        self.embeddings = LiteLLMEmbeddings(
            api_url=config.get("embeddings", {}).get("inference_endpoint"),
            api_key=config.get("embeddings", {}).get("api_key"),
            model_name=config.get("embeddings", {}).get("model_name"),
        )
        self.vectorstore = config.get("vectorstore", {})
        self.language_mapping = {
            "en": "English", "fr": "French", "de": "German",
            "es": "Spanish", "cn": "Chinese", "jp": "Japanese",
        }

    @staticmethod
    def _format_sources(documents):
        unique_sources = []
        seen = set()
        for document in documents:
            source = document.metadata.get("source")
            if source and source not in seen:
                seen.add(source)
                unique_sources.append([source, document.metadata.get("score", 0.0)])
        return unique_sources

    @staticmethod
    def _validate_image(image_data_url):
        if not image_data_url:
            return None
        match = IMAGE_DATA_URL.fullmatch(image_data_url)
        if not match:
            raise ValueError("The attachment must be a JPEG, PNG, or WebP image.")
        try:
            decoded = base64.b64decode(match.group(2), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError("The attached image is not valid base64 data.") from exc
        if len(decoded) > MAX_IMAGE_BYTES:
            raise ValueError("The attached image exceeds the 5 MB limit.")
        return image_data_url

    @staticmethod
    def _request_options(selected_config, *, stream):
        options = {"model": selected_config.get("model_name"), "stream": stream}
        optional_values = {
            "max_tokens": selected_config.get("max_tokens"),
            "temperature": selected_config.get("temperature"),
            "top_p": selected_config.get("top_p"),
            "presence_penalty": selected_config.get("presence_penalty"),
            "frequency_penalty": selected_config.get("frequency_penalty"),
        }
        options.update({key: value for key, value in optional_values.items() if value is not None})
        return options

    async def _translate_to_english(self, client, selected_config, query):
        response = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": self.config.get("translate_system_template", DEFAULT_TRANSLATE_TEMPLATE)},
                {"role": "user", "content": query},
            ],
            **self._request_options(selected_config, stream=False),
        )
        translated = response.choices[0].message.content or ""
        return (translated.replace("English:", "").replace("Answer:", "")
                .replace("English translation:", "").replace("Translation:", "").strip())

    def _create_retriever(self, collection):
        return MilvusRetrieverWithScoreThreshold(
            embedding_function=self.embeddings,
            collection_name=collection,
            collection_description="",
            collection_properties=None,
            connection_args={
                "uri": self.vectorstore.get("uri", "http://localhost:19530"),
                "user": self.vectorstore.get("user", ""),
                "password": self.vectorstore.get("password", ""),
                "db_name": self.vectorstore.get("db_name", "default"),
            },
            consistency_level="Session",
            search_params=None,
            k=int(self.config.get("MAX_RETRIEVED_DOCS", 4)),
            score_threshold=float(self.config.get("SCORE_THRESHOLD", 0.99)),
            enable_dynamic_field=True,
            text_field="page_content",
            logger=self.logger,
        )

    async def stream(self, model, query, collection, collection_full_name, version, language, image=None):
        selected_config = next((item for item in self.llms_config if item.get("name") == model), None)
        if selected_config is None:
            yield {"type": "error", "message": f"Unknown model: {model}"}
            return
        try:
            image = self._validate_image(image)
        except ValueError as exc:
            yield {"type": "error", "message": str(exc)}
            return
        if image and not selected_config.get("supports_vision", False):
            yield {"type": "error", "message": f"{model} is not configured as a vision-capable model."}
            return

        client = AsyncOpenAI(api_key=selected_config.get("api_key"), base_url=selected_config.get("inference_endpoint"))
        retrieval_query = query.strip() or "Analyze the attached image"
        try:
            if language != "en" and query.strip():
                retrieval_query = await self._translate_to_english(client, selected_config, query)
            if collection_full_name != "None" and version != "None":
                retrieval_query = f"We are talking about {collection_full_name}. {retrieval_query}"
            self.logger.info("Collection: %s", collection)
            self.logger.info("Retrieval query: %s", retrieval_query)
            documents = await self._create_retriever(collection).ainvoke("search_query: " + retrieval_query)
        except Exception as exc:
            self.logger.exception("Document retrieval failed")
            yield {"type": "error", "message": f"Document retrieval failed: {exc}"}
            return

        for source, score in self._format_sources(documents):
            yield {"type": "source", "source": source, "score": score}
        references = "\n\n".join(
            f"Reference {index + 1}:\n{document.page_content}"
            for index, document in enumerate(documents)
        ) or "No relevant references were retrieved."
        user_text = f"Question:\n{query or 'Analyze the attached image.'}\n\nReferences:\n{references}"
        user_content = [{"type": "text", "text": user_text}]
        if image:
            user_content.append({"type": "image_url", "image_url": {"url": image}})

        system_template = selected_config.get(
            "system_prompt", self.config.get("system_template", DEFAULT_SYSTEM_TEMPLATE)
        )
        messages = [
            {"role": "system", "content": system_template.format(language=self.language_mapping.get(language, "English"))},
            {"role": "user", "content": user_content},
        ]
        try:
            response = await client.chat.completions.create(
                messages=messages, **self._request_options(selected_config, stream=True)
            )
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {"type": "token", "token": chunk.choices[0].delta.content}
            yield {"type": "job_done"}
        except APIError as exc:
            self.logger.exception("Model API request failed")
            yield {"type": "error", "message": f"Model API request failed: {exc}"}
        except Exception as exc:
            self.logger.exception("Unexpected model streaming error")
            yield {"type": "error", "message": f"Model streaming failed: {exc}"}
