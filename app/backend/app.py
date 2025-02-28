""" Backend for Knowledge Base Chat App """

import json
import logging
import os
import sys
import asyncio

import httpx
from dotenv import dotenv_values, load_dotenv
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

import chatbot
import collections_loader as cl
from helpers import logging_config

# Load local env vars if present
load_dotenv()

# Initialize logger
logging_config()
_logger = logging.getLogger(__name__)

# Get config
config = {
    **dotenv_values(".env"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    **os.environ,  # override loaded values with environment variables
}
_logger.info(f"Config loaded...")

# Load configuration from JSON file
config_file = config.get("CONFIG_FILE")
if config_file and os.path.exists(config_file):
    with open(config_file, "r") as file:
        config_data = json.load(file)
        config.update(config_data)
        _logger.info(f"Configuration loaded from {config_file}")
else:
    _logger.warning(f"Config file {config_file} not found or not specified")

# Get collections, LLMs, vectorstore and embeddings config
collections_config = config.get("collections")
llms_config = config.get("llms")
vectorstore_config = config.get("vectorstore")
embeddings_config = config.get("embeddings")

# Load collections
collections_loader = cl.CollectionsLoader(
    collections_config, vectorstore_config, _logger
)
collections = collections_loader.load_collections()
total_milvus_collections = sum(len(collection.versions) for collection in collections)
_logger.info(
    f"Loaded {total_milvus_collections} versioned collection(s) across {len(collections)} collection(s)"
)

# Initialize Chatbot
chatbot = chatbot.Chatbot(config, _logger)

# App creation
app = FastAPI()

origins = ["*"]
methods = ["*"]
headers = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=methods,
    allow_headers=headers,
)


# Connection Manager for Websockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

#############################
# API Endpoints definitions #
#############################


# Status
@app.get("/health")
async def health():
    """Basic status"""
    return {"message": "Status:OK"}


@app.get("/api/llms")
async def get_llms():
    """Get llms"""
    return llms_config


# Collections
@app.get("/api/collections")
async def get_collections():
    """Get collections"""
    return collections


async def handle_client_request(websocket: WebSocket, data: dict):
    async for next_item in chatbot.stream(
        data["model"],
        data["query"],
        data["collection"],
        data["collection_full_name"],
        data["version"],
        data["language"],
    ):
        answer = json.dumps(next_item)
        await websocket.send_text(answer)


@app.websocket("/ws/query/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            asyncio.create_task(handle_client_request(websocket, data))
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        _logger.info(f"Client {client_id} disconnected")


# Serve React App (frontend)
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        if len(sys.argv) > 1 and sys.argv[1] == "dev":
            # We are in Dev mode, proxy to the React dev server
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://localhost:9000/{path}")
            return Response(response.text, status_code=response.status_code)
        else:
            try:
                return await super().get_response(path, scope)
            except (HTTPException, StarletteHTTPException) as ex:
                if ex.status_code == 404:
                    return await super().get_response("index.html", scope)
                else:
                    raise ex


app.mount("/", SPAStaticFiles(directory="public", html=True), name="spa-static-files")

# Launch the FastAPI server
if __name__ == "__main__":
    from uvicorn import run

    port = int(os.getenv("PORT", "5000"))
    run("app:app", host="0.0.0.0", port=port)
