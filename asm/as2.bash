#!/bin/bash
BASE_PATH=/home/mm/dev/PyDP
if [[ -z "${ASM_PASS2}" ]]; then
  echo "Please start assembler pass 2 manually"
else
  source ${BASE_PATH}/venv/bin/activate
  cd ${BASE_PATH}/asm || exit
  python asm.py as2 "$1" "$2" "$3"
fi

