import datetime


class ExecutionInfo:
    def __init__(self, start=None):
        self.start = start if start else datetime.datetime.now()
        self.end = None
        self.total_seconds = 0
        self.result = None

    def close(self, end=None):
        self.end = end if end else datetime.datetime.now()
        self.total_seconds = (self.end - self.start).total_seconds()

    def __repr__(self):
        return '%s (%s second(s))' % (self.result, self.total_seconds)


def util_exec_time(call, *args, **kwargs):
    execution_info = ExecutionInfo()
    execution_info.result = call(*args, **kwargs)
    execution_info.close()
    return execution_info
