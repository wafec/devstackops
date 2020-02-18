
CREATE TABLE INJECTION (
    INJECTION_ID            INTEGER PRIMARY KEY,
    MESSAGE_ID              INTEGER NOT NULL,
    INJECTION_PARAM         TEXT,
    INJECTION_VALUE         TEXT,
    INJECTION_MUTATION      TEXT,
    INJECTION_OPERATOR      TEXT,
    INJECTION_PARAM_TYPE    TEXT,
    INJECTION_DATE          DATE,
    FOREIGN KEY(MESSAGE_ID) REFERENCES MESSAGE(MESSAGE_ID)
);
/

CREATE TABLE TEST_OUTPUT (
    OUT_ID                  INTEGER PRIMARY KEY,
    TEST_ID                 INTEGER NOT NULL,
    OUT_DATE                DATE,
    OUT_CONTENT             TEXT,
    FOREIGN KEY(TEST_ID) REFERENCES TEST(TEST_ID)
);
/