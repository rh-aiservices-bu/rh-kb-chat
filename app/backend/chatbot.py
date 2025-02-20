import os
from collections.abc import Generator
from queue import Empty, Queue
from threading import Thread

from langchain.callbacks.base import BaseCallbackHandler
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.llms import VLLMOpenAI

from milvus_retriever_with_score_threshold import \
    MilvusRetrieverWithScoreThreshold

import asyncio
from asyncio import Queue as AsyncQueue, QueueEmpty
from concurrent.futures import ThreadPoolExecutor


class QueueCallback(BaseCallbackHandler):
    """Callback handler for streaming LLM responses to an async queue."""

    def __init__(self, q: AsyncQueue, logger):
        self.q = q
        self.logger = logger

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        data = {"type": "token", "token": token}
        await self.q.put(data)

    async def on_llm_end(self, *args, **kwargs) -> None:
        await self.q.put(None)  # Signal the end of the stream


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
        self.llms_config = self.config.get('llms', [])

        # Instantiate LLMs
        self.llm_instances = {}
        for llm in self.llms_config:
            self.llm_instances[llm.get('name')] = VLLMOpenAI(
                openai_api_key=llm.get('api_key'),
                openai_api_base=llm.get('inference_endpoint'),
                model_name=llm.get('model_name'),
                max_tokens=llm.get('max_tokens'),
                top_p=llm.get('top_p'),
                temperature=llm.get('temperature'),
                presence_penalty=llm.get('presence_penalty'),
                streaming=True,
                verbose=False
            )

        # Instantiate Embeddings
        self.embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_url=self.config.get('embeddings').get('inference_endpoint'),
            api_key=self.config.get('embeddings').get('api_key'),
            model_name=self.config.get('embeddings').get('model_name'),
        )

        # Instantiate Vector Store
        self.vectorstore = self.config.get('vectorstore', {})

        # Instantiate Executor    
        self.executor = ThreadPoolExecutor()

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

    async def stream(self, model, query, collection, collection_full_name, version, language):
        """
        Streams the chatbot's response based on the query and other parameters.

        Args:
            query (str): The user's query.
            collection (str): The name of the collection.
            collection_full_name (str): The full name of the product.
            version (str): The version of the product.

        Yields:
            dict: The chatbot's response data.
        """
        # A Queue is needed for Streaming implementation
        q = AsyncQueue()
        job_done = object()

        selected_llm = next((item for item in self.llms_config if item["name"] == model), None)
        if selected_llm:
            llm = VLLMOpenAI(
                openai_api_key=selected_llm.get('api_key'),
                openai_api_base=selected_llm.get('inference_endpoint'),
                model_name=selected_llm.get('model_name'),
                max_tokens=selected_llm.get('max_tokens'),
                top_p=selected_llm.get('top_p'),
                temperature=selected_llm.get('temperature'),
                presence_penalty=selected_llm.get('presence_penalty'),
                streaming=True,
                verbose=False,
                callbacks=[QueueCallback(q, self.logger)]
            )
        else:
            return
        
        translation_model = model
        selected_translation_llm = next((item for item in self.llms_config if item["name"] == translation_model), None)
        if selected_translation_llm:
            llm_translate = VLLMOpenAI(
                openai_api_key=selected_translation_llm.get('api_key'),
                openai_api_base=selected_translation_llm.get('inference_endpoint'),
                model_name=selected_translation_llm.get('model_name'),
                max_tokens=selected_translation_llm.get('max_tokens'),
                top_p=selected_translation_llm.get('top_p'),
                temperature=selected_translation_llm.get('temperature'),
                presence_penalty=selected_translation_llm.get('presence_penalty'),
                streaming=False,
                verbose=False
            )
        else:
            return

        self.logger.info(f"Collection: {collection}")
        self.logger.info(f"Collection Full Name: {collection_full_name}")
        self.logger.info(f"Version: {version}")
        self.logger.info(f"Language: {language}")
        
        retriever = MilvusRetrieverWithScoreThreshold(
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

        language_mapping = {
            "en": "English",
            "fr": "French",
            "de": "German",
            "es": "Spanish",
            "cn": "Chinese",
            "jp": "Japanese",
        }
        
        prompt_value = next((item["prompt"] for item in self.llms_config if item["name"] == model), None)
        prompt_template = prompt_value.format(language=language_mapping.get(language, "English"))
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
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        rag_chain = create_retrieval_chain(retriever, combine_docs_chain)

        # Create a function to call - this will run in a thread
        async def task():
            loop = asyncio.get_event_loop()
            # Translate the query to English if needed
            if language != "en":
                english_query = await loop.run_in_executor(
                    self.executor,
                    llm_translate.invoke,
                    translate_prompt.format(query=query)
                )
                english_query = str(english_query).replace("English:", "").replace("Answer:", "").replace("English translation:", "").replace("Translation:", "").strip().lstrip('\t')
            else:
                english_query = query

            if (collection_full_name != "None") and (version != "None"):
                new_query = f"We are talking about {collection_full_name}. {english_query}"
            else:
                new_query = english_query
            self.logger.info(f"New Query: {new_query}")
            resp = await loop.run_in_executor(
                self.executor,
                rag_chain.invoke,
                {"input": 'search_query: ' + new_query}
            )
            sources = self._format_sources(resp['context'])
            if len(sources) != 0:
                for source in sources:
                    data = {"type": "source", "source": source}
                    await q.put(data)
            await q.put(job_done)

        # Run the task in the background
        asyncio.create_task(task())

        # Get each new item from the queue and yield for our generator
        while True:
            try:
                next_item = await asyncio.wait_for(q.get(), timeout=1.0)
                if next_item is job_done:
                    break
                if isinstance(next_item, dict):
                    yield next_item
            except (QueueEmpty, asyncio.TimeoutError):
                continue
