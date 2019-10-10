from vmbox.shell import *
from vmbox.util import *
import enum


class VmStates(enum.Enum):
    POWERED_OFF = 'powered off'
    RUNNING = 'running'

    def __eq__(self, other):
        if other is None:
            return False
        if isinstance(other, VmStates):
            return super(VmStates, self).__eq__(other)
        return str(other) == self.value


def _machine_any_match(shell_result, condition):
    if shell_result:
        return any(condition(x) for x in shell_result.split('\n'))
    return False


def _machine_get_property_value(content, prop):
    lines = content.split('\n')
    lines = [x for x in lines if x.startswith(prop)]
    if lines:
        line = lines[0]
        values = line.split(':')
        value = ''.join(values[1:])
        return value.strip()
    return None


def _machine_run_command(args_text):
    return shell_run_command('VBoxManage ' + args_text)


def machine_get_state(identifier):
    result = _machine_run_command('showvminfo ' + shell_build_text(identifier))
    state_value = _machine_get_property_value(result, 'State')
    state_value = state_value[:state_value.index('(')]
    return state_value.strip()


def machine_restore(identifier, snapshot):
    result = _machine_run_command('snapshot ' + shell_build_text(identifier) + ' restore ' + shell_build_text(snapshot))
    return _machine_any_match(result, lambda x: x.strip().endswith('100%'))


def machine_start(identifier):
    result = _machine_run_command('startvm ' + shell_build_text(identifier))
    return _machine_any_match(result, lambda x: 'started' in x.strip().lower())


def machine_poweroff(identifier):
    result = _machine_run_command('controlvm ' + shell_build_text(identifier) + ' poweroff')
    return _machine_any_match(result, lambda x: x.strip().endswith('100%'))


id = 'OpenStack Controller'
snap = 'FailureFree'
print('Restore:', machine_restore(id, snap))
print('Start:', util_exec_time(machine_start, id))
print('PowerOff:', machine_poweroff(id))
print('End')