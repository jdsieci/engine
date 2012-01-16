CREATE TABLE "session"(
  session_id character(16) NOT NULL,
  "content" text,
  PRIMARY KEY (session_id),
  UNIQUE (session_id)
)