#!/bin/sh
PORT=${PORT:-8000}
exec micromamba run -n base -- uvicorn app.main:app --host 0.0.0.0 --port $PORT
