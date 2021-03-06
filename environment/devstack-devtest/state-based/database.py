import sqlite3
import multiprocessing
import threading
import datetime


CONNECTION_STRING = 'tests.db'


class DatabaseError(Exception):
    pass


def experiment_add(target):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT IFNULL(MAX(EXP_ID), O) + 1 FROM EXPERIMENT")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO EXPERIMENT (EXP_ID, EXP_TARGET) VALUES (?, ?)", (id, target))
        return id


def test_add(test_number, exp_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT IFNULL(MAX(TEST_ID), 0) + 1 FROM TEST")
        row = cur.fetchone()
        id = row[0]
        cur.execute("INSERT INTO TEST (TEST_ID, TEST_NUMBER, EXP_ID) VALUES (?, ?, ?)", (id, test_number, exp_id))
        return id


def test_change_mode(test_id, test_mode='classic'):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('UPDATE TEST SET TEST_MODE = :TEST_MODE WHERE TEST_ID = :TEST_ID', {
            'TEST_ID': test_id,
            'TEST_MODE': test_mode
        })


def test_get_mode(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('SELECT TEST_MODE FROM TEST WHERE TEST_ID = :TEST_ID', { 'TEST_ID': test_id })
        row = cur.fetchone()
        return row[0]


def test_it_inc(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('UPDATE TEST SET TEST_IT = TEST_IT + 1 WHERE TEST_ID = :TEST_ID', { 'TEST_ID': test_id })


def test_get_it(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('SELECT TEST_IT FROM TEST WHERE TEST_ID = :TEST_ID', { 'TEST_ID': test_id })
        test_it = cur.fetchone()[0]
        return test_it


def test_set_errors(test_id, has_errors):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('UPDATE TEST SET TEST_HAS_ERRORS = ? WHERE TEST_ID = ?', (0 if not has_errors else 1, test_id))


def test_get_errors(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('SELECT TEST_HAS_ERRORS FROM TEST WHERE TEST_ID = ?', [test_id])
        row = cur.fetchone()
        return row[0]


def it_add(test_id, event):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('begin')
        try:
            cur.execute('SELECT IFNULL(MAX(IT_ID), 0) + 1 FROM TEST_ITERATION')
            id = cur.fetchone()[0]
            cur.execute('SELECT TEST_IT FROM TEST WHERE TEST_ID = ?', [test_id])
            number = cur.fetchone()[0]
            cur.execute('INSERT INTO TEST_ITERATION (IT_ID, TEST_ID, IT_NUMBER, IT_EVENT, IT_DATE) VALUES '
                        '(?, ?, ?, ?, ?)', (id, test_id, number, event, datetime.datetime.now()))
            cur.execute('commit')
            return id
        except con.Error as err:
            print('failed it add %s' % repr(err))
            cur.execute('rollback')


def it_register_mode(it_id, mode):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('UPDATE TEST_ITERATION SET IT_MODE = :MODE WHERE IT_ID = :ID', {
            'MODE': mode,
            'ID': it_id
        })


def it_get_current_id(test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        con.isolation_level = None
        cur = con.cursor()
        cur.execute('begin')
        try:
            cur.execute('SELECT I.IT_ID FROM TEST_ITERATION I, TEST T WHERE I.TEST_ID = T.TEST_ID AND T.TEST_ID = ?', [test_id])
            id = cur.fetchone()[0]
            return id
        except con.Error:
            print('failed get current it id')
            cur.execute('rollback')


def message_add(test_id, message_src, message_dst, message_key, message_payload, message_action, message_params_count):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT IFNULL(MAX(MESSAGE_ID), 0) + 1 FROM MESSAGE")
        row = cur.fetchone()
        id = row[0]
        cur.execute('SELECT I.IT_ID FROM TEST T, TEST_ITERATION I WHERE I.TEST_ID = T.TEST_ID AND T.TEST_ID = ? AND T.TEST_IT = I.IT_NUMBER', [test_id])
        row = cur.fetchone()
        if row:
            it_id = row[0]
        else:
            it_id = None
        cur.execute("INSERT INTO MESSAGE "
                    "(MESSAGE_ID, TEST_ID, MESSAGE_SRC, MESSAGE_DST, MESSAGE_KEY, MESSAGE_PAYLOAD, MESSAGE_ACTION, MESSAGE_DATE, IT_ID, MESSAGE_PARAMS_COUNT)"
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (id, test_id, message_src, message_dst, message_key, message_payload, message_action, datetime.datetime.now(), it_id, message_params_count))
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
    with con:
        cur = con.cursor()
        cur.execute("SELECT IFNULL(MAX(INJECTION_ID), 0) + 1 FROM INJECTION")
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


def injection_count_by_test_number(test_number):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('SELECT COUNT(*) FROM INJECTION I, MESSAGE M, TEST T WHERE '
                    'M.TEST_ID = T.TEST_ID AND T.TEST_NUMBER = :TEST_NUMBER AND I.MESSAGE_ID = M.MESSAGE_ID ',
                    { 'TEST_NUMBER': test_number })
        row = cur.fetchone()
        return row[0]


def output_add(test_id, output_content):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        con.isolation_level = None
        cur = con.cursor()
        cur.execute("SELECT IFNULL(MAX(OUT_ID), 0) + 1 FROM TEST_OUTPUT")
        row = cur.fetchone()
        id = row[0]
        cur.execute('SELECT I.IT_ID FROM TEST_ITERATION I, TEST T WHERE T.TEST_ID = I.TEST_ID AND T.TEST_ID = ? AND I.IT_NUMBER = T.TEST_IT', [test_id])
        row = cur.fetchone()
        if row:
            it_id = row[0]
        else:
            it_id = None
        cur.execute("INSERT INTO TEST_OUTPUT (OUT_ID, TEST_ID, OUT_DATE, OUT_CONTENT, IT_ID)"
                    "VALUES"
                    "(?, ? ,?, ?, ?)", (
            id, test_id, datetime.datetime.now(), output_content, it_id
        ))
        return id


def control_add(test_id, state):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute("SELECT IFNULL(MAX(CONTROL_ID), 0) + 1 FROM CONTROL")
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
        cur.execute('SELECT TEST_ID FROM CONTROL ORDER BY CONTROL_DATE DESC')
        row = cur.fetchone()
        if row is None or len(row) == 0:
            return -1
        return row[0]


def logs_add(source, content, test_id):
    con = sqlite3.connect(CONNECTION_STRING)
    with con:
        cur = con.cursor()
        cur.execute('INSERT INTO TEST_LOG (log_content, log_source, test_id, log_date) VALUES '
                    '(?, ?, ?, ?)', (content, source, test_id, datetime.datetime.now()))
