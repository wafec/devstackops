CREATE TABLE CONTROL (
    CONTROL_ID          INTEGER PRIMARY KEY,
    TEST_ID             INTEGER NOT NULL,
    CONTROL_STATE       TEXT,
    CONTROL_DATE        DATE,
    FOREIGN KEY (TEST_ID) REFERENCES TEST(TEST_ID)
);
/