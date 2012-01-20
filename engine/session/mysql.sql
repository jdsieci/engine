CREATE TABLE session(
  session_id VARCHAR(32) PRIMARY KEY,
  expires TIMESTAMP NOT NULL,
  content TEXT
) ENGINE = InnoDB
-- DEFAULT CHARACTER SET = utf8
-- COLLATE = utf8_bin