import subprocess
import sys
import os
import shutil


current_path = os.path.dirname(os.path.abspath(__file__))
t_transitions = []
t_transition_file_path = sys.argv[1]
t_result_path = sys.argv[2]
t_master_setup_path = sys.argv[3]

with open(t_transition_file_path, 'r') as t_transitions_file:
    t_transitions = t_transitions_file.readlines()

t_transitions = [name.replace('\n', '') for name in t_transitions]

if not os.path.exists(t_result_path):
    os.makedirs(t_result_path)

for t_transition in t_transitions:
    dest_path = os.path.join(t_result_path, t_transition)
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    dest_file_path = os.path.join(dest_path, '%s.yaml' % t_transition)
    result_path = os.path.join(dest_path, 'setup.yaml')
    with open(dest_file_path, 'w') as dest_file_file:
        dest_file_file.write('!setup\ngeneric:\n  coverageTransitionSet:\n  - ' + t_transition + '\n')
    candidate_path = os.path.join(dest_path, 'candidates')
    subprocess.run([
       "statemutest.bat", 
        "build",
        t_master_setup_path,
        dest_file_path,
        result_path
        ])
    if not os.path.exists(candidate_path):
        os.makedirs(candidate_path)
    subprocess.run([
        "statemutest.bat",
        "gen",
        result_path,
        candidate_path
    ])
