-- Analysis layer tables

CREATE TABLE analysis_results (
    id              INTEGER PRIMARY KEY,
    analyzer_name   VARCHAR NOT NULL,
    work_id         VARCHAR NOT NULL REFERENCES works(work_id),
    metrics         JSON,
    data            JSON,
    analyzed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (analyzer_name, work_id)
);

CREATE SEQUENCE IF NOT EXISTS seq_analysis_results START 1;

CREATE TABLE word_frequencies (
    work_id VARCHAR NOT NULL REFERENCES works(work_id),
    lemma   VARCHAR NOT NULL,
    count   INTEGER NOT NULL,
    tf      DOUBLE NOT NULL,
    PRIMARY KEY (work_id, lemma)
);

CREATE TABLE pos_distributions (
    work_id VARCHAR NOT NULL REFERENCES works(work_id),
    pos     VARCHAR NOT NULL,
    count   INTEGER NOT NULL,
    ratio   DOUBLE NOT NULL,
    PRIMARY KEY (work_id, pos)
);

CREATE TABLE pos_transitions (
    work_id  VARCHAR NOT NULL REFERENCES works(work_id),
    from_pos VARCHAR NOT NULL,
    to_pos   VARCHAR NOT NULL,
    count    INTEGER NOT NULL,
    ratio    DOUBLE NOT NULL,
    PRIMARY KEY (work_id, from_pos, to_pos)
);

CREATE TABLE sentence_opening_patterns (
    work_id VARCHAR NOT NULL REFERENCES works(work_id),
    pattern VARCHAR NOT NULL,
    count   INTEGER NOT NULL,
    ratio   DOUBLE NOT NULL,
    PRIMARY KEY (work_id, pattern)
);

CREATE TABLE sentiment_scores (
    work_id    VARCHAR NOT NULL REFERENCES works(work_id),
    segment    INTEGER NOT NULL,
    score      DOUBLE NOT NULL,
    label      VARCHAR,
    PRIMARY KEY (work_id, segment)
);

CREATE TABLE character_relations (
    work_id    VARCHAR NOT NULL REFERENCES works(work_id),
    character1 VARCHAR NOT NULL,
    character2 VARCHAR NOT NULL,
    weight     INTEGER NOT NULL,
    PRIMARY KEY (work_id, character1, character2)
);

CREATE TABLE topics (
    topic_id    INTEGER PRIMARY KEY,
    label       VARCHAR,
    top_words   JSON NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS seq_topics START 1;

CREATE TABLE work_topics (
    work_id  VARCHAR NOT NULL REFERENCES works(work_id),
    topic_id INTEGER NOT NULL REFERENCES topics(topic_id),
    weight   DOUBLE NOT NULL,
    PRIMARY KEY (work_id, topic_id)
);

CREATE TABLE style_features (
    work_id      VARCHAR NOT NULL REFERENCES works(work_id),
    feature_name VARCHAR NOT NULL,
    value        DOUBLE NOT NULL,
    PRIMARY KEY (work_id, feature_name)
);

CREATE TABLE author_embeddings (
    work_id   VARCHAR NOT NULL REFERENCES works(work_id),
    dimension INTEGER NOT NULL,
    value     DOUBLE NOT NULL,
    PRIMARY KEY (work_id, dimension)
);

CREATE TABLE ngrams (
    work_id VARCHAR NOT NULL REFERENCES works(work_id),
    n       INTEGER NOT NULL,
    gram    VARCHAR NOT NULL,
    count   INTEGER NOT NULL,
    PRIMARY KEY (work_id, n, gram)
);

CREATE TABLE vocabulary_ages (
    work_id   VARCHAR NOT NULL REFERENCES works(work_id),
    lemma     VARCHAR NOT NULL,
    first_use INTEGER,
    PRIMARY KEY (work_id, lemma)
);

CREATE TABLE dialogue_density (
    work_id VARCHAR NOT NULL REFERENCES works(work_id),
    segment INTEGER NOT NULL,
    ratio   DOUBLE NOT NULL,
    PRIMARY KEY (work_id, segment)
);
