#!/bin/sh
gunicorn app:app -w 2 --threads 10 -b 0.0.0.0:5000