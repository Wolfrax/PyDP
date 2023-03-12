#!/bin/bash
if [[ -z "${ASM_PASS2}" ]]; then
  echo "Please start assembler pass 2 manually"
else
  source /home/mm/dev/PyDP/venv/bin/activate
  python asm.py as2 $1 $2 $3
fi

