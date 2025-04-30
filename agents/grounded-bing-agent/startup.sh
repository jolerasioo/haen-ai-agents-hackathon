#!/bin/bash

# Start Gunicorn
gunicorn app:app --bind=0.0.0.0:8000 --workers=4 --timeout=120 --worker-class=uvicorn.workers.UvicornWorker