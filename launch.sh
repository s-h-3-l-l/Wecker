#!/bin/bash
set -e;

command -v mpv || exit 1;

pip install -r requirements.txt;

if [[ ! -f "alarms.db" ]];
then
    echo ".exit" | sqlite3 -bail -batch -init create-db.sql alarms.db;
fi

mkdir -p bin
wget -O bin/youtube-dl 'https://youtube-dl.org/downloads/latest/youtube-dl'
chmod +x bin/youtube-dl

rm -f mpv.pid;

./service.py &
FLASK_APP=server.py python3 -m flask run --host=0.0.0.0 --port=8000 &
