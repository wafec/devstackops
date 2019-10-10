import subprocess


def _shell_separate_arguments(command):
    i = 0
    quote_found = False
    builder = ''
    while i < len(command):
        c = command[i]
        ignore = False
        if quote_found and c == '\\':
            builder += c
            i += 1
            if i < len(command):
                builder += command[i]
        elif not quote_found and c == '"':
            quote_found = True
        elif quote_found and c == '"':
            quote_found = False
        elif quote_found and c == ' ':
            builder += '&space;'
            ignore = True
        if not ignore:
            builder += c
        i += 1
    values = builder.split(' ')
    values = [x.replace('&space;', ' ') for x in values]
    values = [x[1:-1] if x.startswith('"') and x.endswith('"') else x for x in values]
    return values


def shell_run_command(command):
    result = subprocess.run(_shell_separate_arguments(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            shell=True)
    return result.stdout.decode('iso-8859-1')


def shell_build_text(text):
    return '"' + text + '"'
