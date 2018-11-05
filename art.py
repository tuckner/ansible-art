### Contributed by John Tuckner @tuckner

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import re
import fnmatch
import yaml

from ansible.errors import AnsibleError, AnsibleAction, _AnsibleActionDone, AnsibleActionFail, AnsibleActionSkip
from ansible.executor.powershell import module_manifest as ps_manifest
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.urls import open_url
from ansible.plugins.action import ActionBase

def load_technique(atomic_dir, atomic):
    '''Loads the YAML content of a technique from its directory. (T*)'''

    # Get path to YAML file.
    try:
        file_entry = get_yaml_file_from_dir(atomic_dir + atomic)

        # Load and parses its content.
        with open(file_entry, 'r', encoding="utf-8") as f:
           return yaml.load(f.read())
    except:
        return load_from_git(atomic)

def load_from_git(atomic):
    '''If loading from a file fails, attempt to load from Git'''
    try:
        response = open_url("https://raw.githubusercontent.com/redcanaryco/atomic-red-team/master/atomics/{0}/{0}.yaml".format(atomic))
        return yaml.load(response)
    except HTTPError as e:
        raise AnsibleError("Received HTTP error for %s : %s" % (term, to_native(e)))
    except URLError as e:
        raise AnsibleError("Failed lookup url for %s : %s" % (term, to_native(e)))
    except SSLValidationError as e:
        raise AnsibleError("Error validating the server's certificate for %s: %s" % (term, to_native(e)))
    except ConnectionError as e:
        raise AnsibleError("Error connecting to %s: %s" % (term, to_native(e)))

def get_yaml_file_from_dir(path_to_dir):
    '''Returns path of the first file that matches "*.yaml" in a directory.'''

    for entry in os.listdir(path_to_dir):
        if fnmatch.fnmatch(entry, '*.yaml'):
            # Found the file!
            return os.path.join(path_to_dir, entry)
    self.display.warning("No YAML file describing the technique in {}!".format(path_to_dir))
    return None

def command_list(atomic_test):
    '''Creates list from plaintext set of commands in atomic''' 
    commands = atomic_test['executor'].get("command")
    if commands:
        atomic_test['executor']["command"] = commands.rstrip().split("\n")
    return atomic_test

def replace_vars(parsed_at, args):
    '''Replaces input arguments in atomics with ansible complex arguments'''
    for i, command in enumerate(parsed_at['executor'].get('command')):
        input_arguments = re.findall("#{(.*?)}", command)
        if input_arguments:
            for input_argument in input_arguments:
                default = parsed_at.get("input_arguments")
                command = re.sub("#{%s}" % (input_argument), str(args.get(input_argument, default[input_argument]['default'])), command)
        parsed_at['executor']['command'][i] = command
    return parsed_at

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        ''' handler for file transfer operations '''
        if task_vars is None:
            task_vars = dict()
        atomic = self._task.args.get('atomic')
        if atomic is None:
            raise AnsibleActionFail("Atomic technique is required")
        atomic_dir = self._templar._available_variables.get('atomic_dir')
        executable = self._task.args.get('executable', False)
        tech = load_technique(atomic_dir, atomic)
        run_techniques = []
        for atomic_test in tech['atomic_tests']:
            # Test if Ansible connection is Powershell, then use Windows atomic techniques
            if self._connection._shell.SHELL_FAMILY == "powershell":
                if "windows" in atomic_test['supported_platforms'] and atomic_test['executor'].get('command'):
                    run_techniques.append(atomic_test)
            else:
                if "linux" in atomic_test['supported_platforms'] and atomic_test['executor'].get('command'):
                    run_techniques.append(atomic_test)
        result = super(ActionModule, self).run(tmp, task_vars)
        for technique in run_techniques:
            parsed_at = command_list(technique)
            final_at = replace_vars(parsed_at, self._task.args.get('args'))
            # Run all commands in one task -HACKY-
            for command in final_at['executor']['command']:
                result.update(self._low_level_execute_command(cmd=command, executable=executable))

        return result
