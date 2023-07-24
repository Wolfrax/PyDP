#!/bin/bash
# https://stackoverflow.com/questions/30171050/start-a-process-in-background-do-a-task-then-kill-the-process-in-the-backgroun
# https://stackoverflow.com/questions/12771909/bash-using-trap-ctrlc
# https://www.golinuxcloud.com/capture-ctrl-c-in-bash/

# Call by $ sh start.bash
# This will start the asm_api_server in the background, then run the static http-server.
# Use the link as indicated by output
# To rebuild dist, do $ npm run build

kill_api_server()
{
    kill $serverPID
}

../venv/bin/python ../asm/asm_api_server.py > /dev/null 2>&1 &
serverPID=$!  # Catch the PID for the background process, then trap SIGINT (ctrl-C) and call kill_api_server
trap 'kill_api_server' INT
npm run preview
