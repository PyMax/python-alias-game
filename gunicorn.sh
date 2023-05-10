#!/bin/sh
gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 --threads 50 app:app  -b 0.0.0.0:5000 --reload