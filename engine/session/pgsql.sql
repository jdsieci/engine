CREATE TABLE "session"(
  session_id VARCHAR(32) NOT NULL,
  expires TIMESTAMP NOT NULL,
  "content" text,
  PRIMARY KEY (session_id),
  UNIQUE (session_id)
)