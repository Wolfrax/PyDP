#!/bin/bash
#
# This script uses the environment variable ASM_PASS2 for logic
# - If not set, just echo what to do
# - If set and equal to "exec",then invoke aout_exec.py
# - If set and not equal to "exec".involve asm.py
#

BASE_PATH=/home/mm/dev/PyDP
if [[ -z "${ASM_PASS2}" ]]; then
  # ASM_PASS2 environment variable has zero length, ie not set
  echo "Please start assembler pass 2 manually"
else
  source ${BASE_PATH}/venv/bin/activate
  cd ${BASE_PATH}/asm || exit
  if [[ $ASM_PASS2 == "exec" ]]; then
    echo "Executing as2"
    if [ -z "$4" ]
    then
       python aout_exec.py as2 "$1" "$2" "$3";
    else
      python aout_exec.py as2 "$1" "$2" "$3" "$4";
    fi
  else
    echo "Interpreting as2"
    if [ -z "$4" ]
    then
       python asm.py as2 "$1" "$2" "$3";
    else
      python asm.py as2 "$1" "$2" "$3" "$4";
    fi
  fi


fi

