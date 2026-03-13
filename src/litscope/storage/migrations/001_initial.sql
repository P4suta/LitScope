-- Core data model (created by ingestion layer)

CREATE TABLE works (
    work_id     VARCHAR PRIMARY KEY,
    title       VARCHAR NOT NULL,
    author      VARCHAR NOT NULL,
    pub_year    INTEGER,
    genre       VARCHAR,
    language    VARCHAR DEFAULT 'en',
    word_count  INTEGER,
    sent_count  INTEGER,
    chap_count  INTEGER,
    file_path   VARCHAR NOT NULL,
    file_hash   VARCHAR NOT NULL,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE chapters (
    chapter_id VARCHAR PRIMARY KEY,
    work_id    VARCHAR NOT NULL REFERENCES works(work_id),
    position   INTEGER NOT NULL,
    title      VARCHAR,
    word_count INTEGER,
    sent_count INTEGER
);

CREATE TABLE sentences (
    sentence_id VARCHAR PRIMARY KEY,
    work_id     VARCHAR NOT NULL REFERENCES works(work_id),
    chapter_id  VARCHAR REFERENCES chapters(chapter_id),
    position    INTEGER NOT NULL,
    text        TEXT NOT NULL,
    word_count  INTEGER,
    char_count  INTEGER
);

CREATE TABLE tokens (
    work_id     VARCHAR NOT NULL REFERENCES works(work_id),
    sentence_id VARCHAR NOT NULL REFERENCES sentences(sentence_id),
    position    INTEGER NOT NULL,
    token       VARCHAR NOT NULL,
    lemma       VARCHAR NOT NULL,
    pos         VARCHAR NOT NULL,
    is_stop     BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (work_id, sentence_id, position)
);
