#!/usr/bin/env python3

import os
import signal
import datetime
import json
import time
import sqlite3
import logging
from flask import Flask, request, render_template, redirect
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

DB = sqlite3.connect("alarms.db", check_same_thread=False)

@app.route("/")
def index():
    weekday_names = {
        "mo" : "Monday",
        "di" : "Tuesday",
        "mi" : "Wednesday",
        "do" : "Thursday",
        "fr" : "Friday",
        "sa" : "Saturday",
        "so" : "Sunday"
    }
    alarms = []
    sounds = []
    now = datetime.datetime.now()
    
    cursor = DB.cursor()
    
    for rowid, weekdays, hour, minute, sound in cursor.execute("SELECT rowid, weekdays, hour, minute, sound FROM Alarms ORDER BY rowid ASC;"):
        weekdays = json.loads(weekdays)
        weekdays = ", ".join(map(lambda s: weekday_names[s], filter(lambda x: weekdays[x], weekdays)))
        alarms.append({
            "value" : f"{weekdays} {hour:02d}:{minute:02d} {sound}",
            "id" : rowid
        })
        
    for rowid, name in cursor.execute("SELECT rowid, name FROM Sounds ORDER BY rowid ASC;"):
        sounds.append({
            "value" : name,
            "id" : rowid
        })
        
    cursor.close()
    
    return render_template(
        "index.html",
        alarms=alarms,
        hour=now.hour,
        minute=now.minute,
        weekday=now.date().weekday(),
        sounds=sounds,
        is_ringing=os.path.isfile("mpv.pid")
    )

@app.route("/create", methods=["POST"])
def create():
    weekdays = {
        "mo" : False,
        "di" : False,
        "mi" : False,
        "do" : False,
        "fr" : False,
        "sa" : False,
        "so" : False
    }
    try:
        hour = request.form["hour"]
        minute = request.form["minute"]
        sound = request.form["sound"]
    except KeyError:
        return "Bad request", 400
    
    for key in weekdays:
        if key in request.form:
            weekdays[key] = True
            
    if not any(weekdays.values()):
        return "Bad request", 400
            
    try:
        hour = int(hour, 10)
        minute = int(minute, 10)
    except ValueError:
        return "Bad request", 400
    
    sound = str(sound)
    weekdays = json.dumps(weekdays)
    
    cursor = DB.cursor()
    cursor.execute(
        """
        SELECT 1 FROM Sounds WHERE name = ?;
        """,
        (sound,)
    )
    
    if cursor.fetchone() is None:
        return "Bad request", 400
    
    cursor.execute(
        """
        INSERT INTO Alarms (weekdays, hour, minute, sound) VALUES (?, ?, ?, ?);
        """,
        (weekdays, hour, minute, sound)
    )
    
    cursor.close()
    DB.commit()
    
    return redirect("/")
    
@app.route("/delete", methods=["POST"])
def delete():
    try:
        id = int(request.form["id"], 10)
    except (ValueError, KeyError):
        return "Bad request", 400
        
    cursor = DB.cursor()
    cursor.execute(
        """
        DELETE FROM Alarms WHERE rowid = ?;
        """,
        (id,)
    )
    
    cursor.close()
    DB.commit()
    
    return redirect("/")

@app.route("/stop", methods=["GET"])
def stop():
    if os.path.isfile("mpv.pid"):
        pid = None
        
        with open("mpv.pid") as f:
            pid = int(f.read(), 10)
            
        os.kill(pid, signal.SIGKILL)
        
        while os.path.isfile("mpv.pid"):
            time.sleep(0.2)
            
    return redirect("/")
