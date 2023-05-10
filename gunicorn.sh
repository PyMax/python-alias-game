#!/bin/sh
gunicorn app:app -w 1 --threads 100 -b 0.0.0.0:5000 --reload