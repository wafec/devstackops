from requests.exceptions import HTTPError


def util_handle_response(response, callback=None, error_callback=None, *args, **kwargs):
    try:
        response.raise_for_status()
        data = response.json()
        if callback:
            callback_result = callback(data, response, *args, **kwargs)
            data = callback_result if callback_result else data
        return data
    except HTTPError as http_err:
        # TODO: log errors here
        if error_callback:
            error_callback(http_err, *args, **kwargs)
        pass
    except Exception as err:
        # TODO: log errors here
        pass
    return None