#!/bin/bash

set -x

#### ssh-keys added as part of the script will be used to authenticate 
#### for cloning any dependent repositories

# Created a ssh agent and loading the agent to add ssh keys
ssh-agent >> agent.sh && source agent.sh

# Adding ssh key
ssh-add - <<< "${GIT_PRIVATE_KEY}"
