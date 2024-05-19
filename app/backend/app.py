""" Backend for Knowledge Base Chat App """
import hashlib
import logging
import os
import sys
import time
from typing import List
import json

import boto3
import chatbot
import httpx
from app_config import LOG_LEVELS, LOGGING_CONFIG
from dotenv import dotenv_values, load_dotenv
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from uvicorn import run
from fastapi import HTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

# Load local env vars if present
load_dotenv()

# Initialize logger
logger = logging.getLogger("app")

# Get config
config = {
    **dotenv_values(".env"),  # load shared development variables
    **dotenv_values(".env.secret"),  # load sensitive variables
    **os.environ,  # override loaded values with environment variables
}
logger.info(f'Config loaded...')

# Load collections from JSON file
with open(config['MILVUS_COLLECTIONS_FILE'], 'r') as file:
    collections_data = json.load(file)

# Load Prompt template from txt file
with open(config['PROMPT_FILE'], 'r') as file:
    prompt_template = file.read()
    config["PROMPT_TEMPLATE"] = prompt_template

# Initialize Chatbot
chatbot = chatbot.Chatbot(config, logger)

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
    allow_headers=headers
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
    """ Basic status """
    return {"message": "Status:OK"}

# Collections
@app.get("/api/collections")
async def get_collections():
    """ Get collections """
    return collections_data

# Query (chatbot exchanges are handled through websocket for streaming)
@app.websocket("/ws/query/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
      while True:
          data = await websocket.receive_text()
          data = json.loads(data)
          for next_item in chatbot.stream(data["query"], data["collection"], data["product_full_name"], data["version"], data["language"]):
              answer = json.dumps(next_item)
              await websocket.send_text(answer)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Client {client_id} disconnected")

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
    port = int(os.getenv('PORT', '5000'))
    run(app, host="0.0.0.0", port=port)
