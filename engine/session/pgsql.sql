CREATE TABLE "session"(
  session_id character(33) NOT NULL,
  expires TIMESTAMP NOT NULL,
  "content" text,
  PRIMARY KEY (session_id),
  UNIQUE (session_id)
)