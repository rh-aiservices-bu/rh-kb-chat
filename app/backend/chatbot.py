import time
import os
from collections.abc import Generator
from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import RetrievalQA
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import VLLMOpenAI
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import Milvus
from milvus_retriever_with_score_threshold import MilvusRetrieverWithScoreThreshold
from queue import Empty, Queue
from threading import Thread


class QueueCallback(BaseCallbackHandler):
    """Callback handler for streaming LLM responses to a queue."""

    def __init__(self, q, logger):
        self.q = q
        self.logger = logger

    def on_llm_new_token(self, token: str, **kwargs: any) -> None:
        data = {"type": "token", "token": token}
        self.q.put(data)

    def on_llm_end(self, *args, **kwargs: any) -> None:
        return self.q.empty()


class Chatbot:
    """
    A class representing a chatbot.

    Args:
        config (dict): Configuration settings for the chatbot.
        logger: Logger object for logging messages.

    Attributes:
        logger: Logger object for logging messages.
        config (dict): Configuration settings for the chatbot.
        model_kwargs (dict): Keyword arguments for the model.
        embeddings: HuggingFaceEmbeddings object for handling embeddings.
        prompt_template: Template for the chatbot's prompt.

    Methods:
        _format_sources: Formats the list of sources.
        stream: Streams the chatbot's response based on the query and other parameters.
    """

    def __init__(self, config, logger):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        self.logger = logger
        self.config = config
        self.model_kwargs = {"trust_remote_code": True}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config["EMBEDDINGS_MODEL_NAME"],
            model_kwargs=self.model_kwargs,
            show_progress=False,
        )
        self.prompt_template = config["PROMPT_TEMPLATE"]

    def _format_sources(self, sources_list):
        """
        Formats the list of sources.

        Args:
            sources_list (list): List of sources.

        Returns:
            list: Unique list of sources.
        """
        unique_list = []
        for item in sources_list:
            if item.metadata['source'] not in unique_list:
                unique_list.append(item.metadata['source'])
        return unique_list

    def stream(self, query, collection, product_full_name, version, language) -> Generator:
        """
        Streams the chatbot's response based on the query and other parameters.

        Args:
            query (str): The user's query.
            collection (str): The name of the collection.
            product_full_name (str): The full name of the product.
            version (str): The version of the product.

        Yields:
            dict: The chatbot's response data.
        """
        # A Queue is needed for Streaming implementation
        q = Queue()
        job_done = object()

        llm = VLLMOpenAI(
            openai_api_key="EMPTY",
            openai_api_base=self.config["INFERENCE_SERVER_URL"],
            model_name=self.config["MODEL_NAME"],
            max_tokens=int(self.config["MAX_TOKENS"]),
            top_p=float(self.config["TOP_P"]),
            temperature=float(self.config["TEMPERATURE"]),
            presence_penalty=float(self.config["PRESENCE_PENALTY"]),
            streaming=True,
            verbose=False,
            callbacks=[QueueCallback(q, self.logger)],
        )

        llm_translate = VLLMOpenAI(
            openai_api_key="EMPTY",
            openai_api_base=self.config["INFERENCE_SERVER_URL"],
            model_name=self.config["MODEL_NAME"],
            max_tokens=256,
            top_p=0.1,
            temperature=0.1,
            presence_penalty=1.03,
            streaming=False,
            verbose=False
        )

        retriever = MilvusRetrieverWithScoreThreshold(
            embedding_function=self.embeddings,
            collection_name=collection,
            collection_description="",
            collection_properties=None,
            connection_args={
                "host": self.config.get("MILVUS_HOST", "default_host"),
                "port": self.config.get("MILVUS_PORT", "default_port"),
                "user": self.config.get("MILVUS_USERNAME", "default_username"),
                "password": self.config.get("MILVUS_PASSWORD", "default_password"),
            },
            consistency_level="Session",
            search_params=None,
            k=int(self.config.get("MAX_RETRIEVED_DOCS", 4)),
            score_threshold=float(self.config.get("SCORE_THRESHOLD", 0.99)),
            metadata_field="metadata",
            text_field="page_content",
            logger=self.logger,
        )

        language_mapping = {
            "en": "English",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "cn": "Chinese",
            "jp": "Japanese",
        }
        
        prompt_template = self.prompt_template.format(language=language_mapping.get(language, "English"))
        prompt = PromptTemplate.from_template(prompt_template)

        translate_prompt = """
        <s>[INST] <<SYS>>
        Translate the following text to English. Only translate the text as concisely as possible. Don't add any comment or information.
        If the text is already in English, don't change it or apologize, just copy it without any other mention.
        <</SYS>>
        Text to translate:
        {query}
        """

        # Instantiate RAG chain
        rag_chain = RetrievalQA.from_chain_type(
            llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True,
        )

        # Create a function to call - this will run in a thread
        def task():
            # Translate the query to English if needed
            if language != "en":
                english_query = str(llm_translate.invoke(translate_prompt.format(query=query))).replace("English:", "").replace("Answer:", "").replace("English translation:", "").replace("Translation:", "").strip().lstrip('\t')
            else:
                english_query = query

            if (product_full_name != "None") and (version != "None"):
                new_query = f"We are talking about {product_full_name}. {english_query}"
            else:
                new_query = english_query
            self.logger.info(f"Query: {new_query}")
            resp = rag_chain.invoke({"query": new_query})
            sources = self._format_sources(resp['source_documents'])
            if len(sources) != 0:
                for source in sources:
                    data = {"type": "source", "source": source}
                    q.put(data)
            q.put(job_done)

        # Create a thread and start the function
        t = Thread(target=task)
        t.start()

        # Get each new item from the queue and yield for our generator
        while True:
            try:
                next_item = q.get(True, timeout=1)
                if next_item is job_done:
                    break
                if isinstance(next_item, dict):
                    yield next_item
            except Empty:
                continue
