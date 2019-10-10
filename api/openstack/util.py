from requests.exceptions import HTTPError
import time
import datetime


def util_handle_response(response, callback=None, error_callback=None, *args, **kwargs):
    try:
        response.raise_for_status()
        try:
            data = response.json()
        except Exception:
            data = True
        if callback:
            callback_result = callback(data, response, *args, **kwargs)
            data = callback_result if callback_result else data
        return data
    except HTTPError as http_err:
        # TODO: log errors here
        if error_callback:
            error_callback(http_err, response, *args, **kwargs)
        pass
    except Exception as err:
        # TODO: log errors here
        pass
    return None


def util_wait(condition, timeout, *args, **kwargs):
    start = datetime.datetime.now()
    while not condition(*args, **kwargs) and (datetime.datetime.now() - start).total_seconds() < timeout:
        time.sleep(0.5)
    return condition(*args, **kwargs)