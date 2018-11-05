# About

This is an Ansible Action Plugin to run Atomics from the Atomic Red Team project. Ansible will detect the remote operating system, gather commands needed to be run for the technique given, remote to the device, and execute the commands via
Ansible's 'raw' command execution.

# Installation

Add 'art.py' to your Ansible installation in the action plugin directory or your custom action plugin directory.

```
/ansible/lib/ansible/plugins/action
```

# Running Ad-hoc Atomics

Example playbook `example-playbook.yml` included. Provide the atomic to be tested and relevant parameters to pass to the atomic shown in the example.

```
ansible-playbook example-playbook.yml
```

Set the 'atomic_dir' variable in your playbook to use a local version of
atomic red team atomics rather than pull from Github.

# Running & Creating Specific Atomic Playbooks

Ansible has the ability to run commands in a structured format instead of raw input, but this requires specific playbooks to be created to issue commands related to the atomic.  This is time consuming and thus this 'ad-hoc' way of running playbooks can suffice if there are no playbooks created for the technique you wish to run.

## Referenced Projects

https://github.com/ansible/ansible
https://github.com/redcanaryco/atomic-red-team
