# !/bin/sh

export FLASK_DEBUG=1
export FLASK_APP=catan/server
export FLASK_RUN_HOST=0.0.0.0

flask run --port 6969