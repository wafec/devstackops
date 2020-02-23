import sqlite3
import multiprocessing
import datetime


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
                    "(MESSAGE_ID, TEST_ID, MESSAGE_SRC, MESSAGE_DST, MESSAGE_KEY, MESSAGE_PAYLOAD, MESSAGE_ACTION, MESSAGE_DATE)"
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (id, test_id, message_src, message_dst, message_key, message_payload, message_action, datetime.datetime.now()))
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
                        "INJECTION_MUTATION, INJECTION_PARAM_TYPE, INJECTION_OPERATOR, INJECTION_DATE) VALUES ("
                        "?, ?, ?, ?, ?, ?, ?, ?)", (
                id, message_id, injection_param, str(injection_value), injection_mutation, injection_param_type, injection_operator, datetime.datetime.now()
            ))
        except sqlite3.InterfaceError:
            try:
                cur.execute("INSERT INTO INJECTION (INJECTION_ID, MESSAGE_ID, INJECTION_PARAM, INJECTION_VALUE, "
                            "INJECTION_MUTATION, INJECTION_PARAM_TYPE, INJECTION_OPERATOR, INJECTION_DATE) VALUES ("
                            "?, ?, ?, ?, ?, ?, ?, ?)", (
                                id, message_id, injection_param, 'Could not add value', injection_mutation,
                                injection_param_type, injection_operator, datetime.datetime.now()
                            ))
            except:
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


def output_add(test_id, output_content):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT MAX(IFNULL(OUT_ID, 0)) + 1 FROM TEST_OUTPUT")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO TEST_OUTPUT (OUT_ID, TEST_ID, OUT_DATE, OUT_CONTENT)"
                    "VALUES"
                    "(?, ? ,?, ?)", (
            id, test_id, datetime.datetime.now(), output_content
        ))
        return id


def control_add(test_id, state):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT MAX(IFNULL(CONTROL_ID, 0)) + 1 FROM CONTROL")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO CONTROL (CONTROL_ID, TEST_ID, CONTROL_STATE, CONTROL_DATE) VALUES (?, ?, ?, ?)", (id, test_id, state, datetime.datetime.now()))
        return id


def control_update(test_id, state):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("UPDATE CONTROL SET CONTROL_STATE = :CONTROL_STATE, CONTROL_DATE = :CONTROL_DATE WHERE TEST_ID = :TEST_ID", {
            'CONTROL_STATE': state,
            'TEST_ID': test_id,
            'CONTROL_DATE': datetime.datetime.now()
        })


def control_ret_state(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('SELECT CONTROL_STATE FROM CONTROL WHERE TEST_ID = :TEST_ID '
                    'ORDER BY CONTROL_DATE DESC', {
            'TEST_ID': test_id
        })
        row = cur.fetchone()
        state = row[0]
        return state


def control_ret_last_test_id():
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('SELECT IFNULL(TEST_ID, -1) FROM CONTROL ORDER BY CONTROL_DATE DESC')
        row = cur.fetchone()
        return row[0]
