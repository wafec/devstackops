import sqlite3
import multiprocessing


CONNECTION_STRING = 'tests.db'
MESSAGE_ADD_LOCK = multiprocessing.Lock()
INJECTION_ADD_LOCK = multiprocessing.Lock()


class DatabaseError(Exception):
    pass


def experiment_add(target):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT MAX(IFNULL(EXP_ID, 0)) + 1 FROM EXPERIMENT")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO EXPERIMENT (EXP_ID, EXP_TARGET) VALUES (?, ?)", (id, target))
        return id


def test_add(test_number, exp_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT MAX(IFNULL(TEST_ID, 0)) + 1 FROM TEST")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO TEST (TEST_ID, TEST_NUMBER, EXP_ID) VALUES (?, ?, ?)", (id, test_number, exp_id))
        return id


def message_add(test_id, message_src, message_dst, message_key, message_payload, message_action):
    con = sqlite3.connect(CONNECTION_STRING)
    with con, MESSAGE_ADD_LOCK:
        cur = con.cursor()
        cur.execute("SELECT MAX(IFNULL(MESSAGE_ID, 0)) + 1 FROM MESSAGE")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO MESSAGE "
                    "(MESSAGE_ID, TEST_ID, MESSAGE_SRC, MESSAGE_DST, MESSAGE_KEY, MESSAGE_PAYLOAD, MESSAGE_ACTION)"
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (id, test_id, message_src, message_dst, message_key, message_payload, message_action))
        return id


def injection_list_params(test_number):
    con = sqlite3.connect(CONNECTION_STRING)
    result = None
    with con:
        cur = con.cursor()
        cur.execute("SELECT I.INJECTION_PARAM, I.INJECTION_OPERATOR, I.INJECTION_PARAM_TYPE "
                    "FROM INJECTION I, TEST T, MESSAGE M "
                    "WHERE T.TEST_NUMBER = :TEST_NUMBER AND T.TEST_ID = M.TEST_ID AND I.MESSAGE_ID = M.MESSAGE_ID ",
                    { 'TEST_NUMBER': test_number })
        rows = cur.fetchall()
        result = [{ 'injection_param': row[0], 'injection_operator': row[1], 'injection_param_type': row[2] } for row in rows]
    return result


def injection_add(message_id, injection_param, injection_value, injection_mutation, injection_param_type, injection_operator):
    con = sqlite3.connect(CONNECTION_STRING)
    result = None
    with con, INJECTION_ADD_LOCK:
        cur = con.cursor()
        cur.execute("SELECT MAX(IFNULL(INJECTION_ID, 0)) + 1 FROM INJECTION")
        row = cur.fetchone()
        id = row[0]
        try:
            cur.execute("INSERT INTO INJECTION (INJECTION_ID, MESSAGE_ID, INJECTION_PARAM, INJECTION_VALUE, "
                        "INJECTION_MUTATION, INJECTION_PARAM_TYPE, INJECTION_OPERATOR) VALUES ("
                        "?, ?, ?, ?, ?, ?, ?)", (
                id, message_id, injection_param, injection_value, injection_mutation, injection_param_type, injection_operator
            ))
        except sqlite3.InterfaceError:
            raise DatabaseError()
        return id


def injection_count(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM INJECTION I, MESSAGE M WHERE "
                    "M.TEST_ID = :TEST_ID AND I.MESSAGE_ID = M.MESSAGE_ID ", {
            'TEST_ID': test_id
        })
        row = cur.fetchone()
        return row[0]