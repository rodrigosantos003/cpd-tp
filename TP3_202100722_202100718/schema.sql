-- USERS
DROP TABLE IF EXISTS user;
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    name TEXT,
    email TEXT,
    username TEXT,
    password TEXT
);

-- Passwords hashed with bcrypt
INSERT INTO user VALUES (null, 'Homer Simpson', 'homer@simpsons.org', 'homer', '$2b$12$5Q13aQxNNtpgFa1xaaTNhOsuQ7zY9g3ntvMUTaglL/ybnjx9qq8Hy');
INSERT INTO user VALUES (null, 'Bart Simpson', 'bart@simpsons.org', 'bart', '$2b$12$TTkxfPKJoo1L6ZzOTjY9QOapQal0IpVy2Fz5dB.rLQzM1sISiCVO6');
INSERT INTO user VALUES (null, 'Lisa Simpson', 'lisa@simpsons.org', 'lisa', '1234');
INSERT INTO user VALUES (null, 'Marge Simpson', 'marge@simpsons.org', 'marge', '1234');
INSERT INTO user VALUES (null, 'Maggie Simpson', 'maggie@simpsons.org', 'maggie', '1234');


-- PROJECTS
DROP TABLE IF EXISTS project;
CREATE TABLE project (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT,
    creation_date TEXT,
    last_updated TEXT,
    FOREIGN KEY(user_id) REFERENCES user(id)
);

INSERT INTO project VALUES (null, 1, 'Doughnuts', '2020-05-01', '2020-06-01');
INSERT INTO project VALUES (null, 1, 'Eat well', '2020-05-01', '2020-05-02');
INSERT INTO project VALUES (null, 2, 'Save the world!', '2020-05-07', '2020-06-01');


-- TASKS
DROP TABLE IF EXISTS task;
CREATE TABLE task (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    manager_id INTEGER,
    title TEXT,
    creation_date TEXT,
    completed INTEGER,
    FOREIGN KEY(project_id) REFERENCES project(id)
    FOREIGN KEY(manager_id) REFERENCES user(id)
);

INSERT INTO task VALUES (null, 1, 1, 'Search for doughnuts', '2020-05-05', 1);
INSERT INTO task VALUES (null, 1, 1, 'Eat cream', '2020-05-05', 0);
INSERT INTO task VALUES (null, 2, 1, 'Eat vegetables everyday', '2020-05-10', 1);
INSERT INTO task VALUES (null, 2, 1, 'Eat doughnuts everyday', '2020-05-11', 1);
INSERT INTO task VALUES (null, 2, 1, 'Eat lots of sugar', '2020-05-12', 0);
INSERT INTO task VALUES (null, 3, 2, 'See who needs to be saved', '2020-05-07', 0);
INSERT INTO task VALUES (null, 3, 2, 'Save those who needs to be saved', '2020-05-07', 0);
INSERT INTO task VALUES (null, 3, 2, 'Save those from being not saved', '2020-05-08', '1');

-- COLLABORATORS

DROP TABLE IF EXISTS collaborator;
CREATE TABLE collaborator (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    user_id INTEGER,
    FOREIGN KEY(project_id) REFERENCES project(id),
    FOREIGN KEY(user_id) REFERENCES user(id)
);