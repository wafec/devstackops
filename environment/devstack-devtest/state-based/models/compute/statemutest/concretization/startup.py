import os
import sys
import subprocess


if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2]
    level = sys.argv[3]
    summaries = []
    for path, subdirs, files in os.walk(src):
        for name in files:
            if '-summary-' in name:
                summaries.append(os.path.join(path, name))
    if summaries:
        if not os.path.exists(dst):
            os.makedirs(dst)
        subprocess.run([
            'python',
            'concretization.py',
            dst
            ] + summaries + [
            '--zero',
            '--level',
            level
        ])