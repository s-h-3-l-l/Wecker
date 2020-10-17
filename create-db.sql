PRAGMA foreign_keys = ON;

CREATE TABLE Sounds (
    name TEXT PRIMARY KEY NOT NULL,
    path TEXT NOT NULL
);

CREATE TABLE Alarms (
    weekdays TEXT NOT NULL,
    hour INTEGER NOT NULL CHECK(hour >= 0 AND hour < 24),
    minute INTEGER NOT NULL CHECK(minute >= 0 AND minute < 60),
    sound TEXT NOT NULL,
    FOREIGN KEY(sound) REFERENCES Sounds(name) ON DELETE CASCADE
);

-- Some defaults

INSERT INTO Sounds (name, path) VALUES ('Bell', 'alarms/beep.mp3');
INSERT INTO Sounds (name, path) VALUES ('LoFi Radio', 'https://www.youtube.com/watch?v=5qap5aO4i9A');
INSERT INTO Sounds (name, path) VALUES ('Jazz Radio', 'https://www.youtube.com/watch?v=DSGyEsJ17cI');
INSERT INTO Sounds (name, path) VALUES ('Beethoven 6. Sinfonie', 'alarms/beethoven-6.mp3');
