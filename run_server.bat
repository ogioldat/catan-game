@echo off
set FLASK_DEBUG=1
set FLASK_APP=catan/server
set FLASK_RUN_HOST=0.0.0.0

flask run --port 6969