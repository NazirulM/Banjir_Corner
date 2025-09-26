-- create a new table
CREATE TABLE "user" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    email VARCHAR(255),
    password TEXT,
    age INT
);

-- permanently drop table
DROP TABLE IF EXISTS profile;

--insert data into table
INSERT INTO "user"(name, email, age, password) VALUES
    ('Trump', 'shibal@gmail.com', 100, '56239'),
    ('Bolivia', 'woman@gmail.com', 21, 'abc123');

SELECT * FROM "user";

-- query the name from user table with condition of age
SELECT name FROM "user"
WHERE age > 50;

-- update specific rows in a table 
--(must use WHERE statement to avoid whole column to be affected)
UPDATE "user" SET email = 'shibalsekki@gmail.com' 
WHERE id = 1;

INSERT INTO "user"(name, email, age, password) VALUES 
    ('Rei', 'rei_ive@gmail.com', 21, 'bob981'),
    ('Kamikei', 'kamisama@yahoo.com', 33, 'popopo811');

-- delete records from table
-- (must use WHERE statement to avoid whole records to be removed)
DELETE FROM "user" WHERE name = 'Trump' AND age > 50;

-- edit columns for a table (add, modify data type, delete)
ALTER TABLE "user" ADD gender VARCHAR(255);
ALTER TABLE "user" ALTER COLUMN gender TYPE TEXT;
ALTER TABLE "user" DROP COLUMN gender;







