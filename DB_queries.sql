-- create a new table
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    password TEXT,
    age INT
);

-- permanently drop table
DROP TABLE profile;

--insert data into table
INSERT INTO "user"(name, email age, password) VALUES (
    ('Trump', 'shibal@gmail.com', 100, '56239')
);