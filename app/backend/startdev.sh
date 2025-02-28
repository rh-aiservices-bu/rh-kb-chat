#!/bin/bash
source /home/gmoutier/Dev/repos/rh-aiservices-bu/rh-kb-chat/app/backend/.venv/bin/activate
watchmedo auto-restart --pattern "*.py" --recursive --signal SIGTERM python app.py