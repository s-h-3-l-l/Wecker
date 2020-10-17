#!/usr/bin/env python3

import os
import time
import json
import sqlite3
import datetime
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Thread
from queue import Queue

EVENT_QUEUE = Queue()

class Alarm:
    def __init__(self, weekdays, hour, minute, path):
        self.weekdays = weekdays
        self.hour = hour
        self.minute = minute
        self.path = path

class AlarmThread(Thread):
    def __init__(self):
        super().__init__()
        self._db = sqlite3.connect("alarms.db", check_same_thread=False)
        self._run_mpv = False
        self._run = True
        self._alarms = []
        self._reload = True
    
    def _get_alarms(self):
        weekdays = {
            "mo" : 0,
            "di" : 1,
            "mi" : 2,
            "do" : 3,
            "fr" : 4,
            "sa" : 5,
            "so" : 6 
        }
        self._alarms = []
        cursor = self._db.cursor()
        
        for weekday, hour, minute, sound_path in cursor.execute("SELECT a.weekdays, a.hour, a.minute, s.path FROM Alarms AS a JOIN Sounds AS s ON a.sound = s.name;"):
            weekday = json.loads(weekday)
            weekday = list(map(lambda s: weekdays[s], filter(lambda x: weekday[x], weekday)))
            self._alarms.append(Alarm(weekday, hour, minute, sound_path))
            
        cursor.close()
    
    def _wait_for_alarm(self, point, path):
        while datetime.datetime.now() < point and self._run and not self._reload:
            time.sleep(30)
            
        if not self._run or self._reload:
            return
            
        self._run_mpv = True
        env = os.environ
        env["PATH"] = f"./bin:{env['PATH']}"
        proc = subprocess.Popen(
            ["mpv", "--loop", "--vid=no", "--no-resume-playback", "--no-terminal", "--", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
        pid_file = "mpv.pid"
        
        with open(pid_file, "w") as f:
            f.write(f"{proc.pid}")
        
        while self._run_mpv and proc.poll() is None:
            time.sleep(1)
        
        if proc.poll() is None:
            proc.kill()
        
        os.remove(pid_file)
        
        self._run_mpv = False
    
    def run(self):
        while self._run:
            if self._reload:
                self._get_alarms()
                self._reload = False
            
            now = datetime.datetime.now()
            to_run = list(filter(lambda x: now.date().weekday() in x.weekdays and (now.hour, now.minute) < (x.hour, x.minute), self._alarms))
            
            for alarm in sorted(to_run, key=lambda x: (x.hour, x.minute)):
                self._wait_for_alarm(now.replace(hour=alarm.hour, minute=alarm.minute, second=0), alarm.path)
            
            if self._run and not self._reload:
                time.sleep(30)
        
    def stop(self):
        self._run = False
        super().join()
        
    def stop_alarm(self):
        self._run_mpv = False
        
    def reload(self):
        self._reload = True

class WatchDogThread(FileSystemEventHandler):        
    def on_modified(self, event):
        global EVENT_QUEUE
        EVENT_QUEUE.put("reload")

def main():
    global EVENT_QUEUE
    
    alarm_thread = AlarmThread()
    observer = Observer()
    observer.schedule(WatchDogThread(), "alarms.db")
    
    alarm_thread.start()
    observer.start()
    
    try:
        while True:
            event = EVENT_QUEUE.get()
            
            if event == "reload":
                alarm_thread.reload()
            elif event == "stop":
                alarm_thread.stop_alarm()
    finally:
        observer.stop()
        observer.join()
        alarm_thread.stop()

if __name__ == "__main__":
    main()
