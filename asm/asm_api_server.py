from flask import Flask, request, jsonify
import asm
import threading
import queue
import logging
from logging.handlers import QueueHandler
from flask_sock import Sock
import os

app = Flask(__name__)

# https://blog.miguelgrinberg.com/post/add-a-websocket-route-to-your-flask-2-x-application
sock = Sock(app)


class Session:
    def __init__(self):
        self.vm = None
        self.breakLines = []
        self.goThread = None
        self.goThreadBreak = False
        self.cmd = None
        self.trace = False
        self.trace_fn = 'trace.txt'
        self.verbose = False

        self.logger = logging.getLogger('pyPDP')

        # Set environment variables, this will avoid doing os.execv or sys.exit.
        os.environ['ASM_EXEC'] = '1'
        os.environ['ASM_EXIT'] = '1'

        self.log_queue = queue.Queue(-1)  # Infinite size
        fmt = logging.Formatter('%(asctime)s - %(message)s')

        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(fmt)

        self.logger.addHandler(queue_handler)

        self.logger.info('New session')


session = None


@app.route('/asm/vm/PSW')
def PSW():
    if session.vm:
        return jsonify(session.vm.PSW.get())
    return jsonify([])


@app.route('/asm/vm/registers')
def registers():
    if session.vm:
        return jsonify(session.vm.register)
    return jsonify([])


@app.route('/asm/vm/stack')
def stack():
    if session.vm:
        return jsonify(list(zip(session.vm.stack_read_addr(), session.vm.stack_read())))
    return jsonify([])


@app.route('/asm/vm/variables')
def variables():
    vars = []
    if session.vm:
        for k, v in session.vm.variables.table.items():
            vars.append([k, v])
    return jsonify(vars)

@app.route('/asm/vm/labels')
def labels():
    lbls = []
    if session.vm:
        for key, addr in session.vm.named_labels.table.items():
            val = session.vm.mem.read(addr, 2)
            lbls.append([key, str(addr).zfill(4), hex(val)])
    return jsonify(lbls)


@app.route('/asm/vm/sysstatus')
def sysstatus():
    if session.vm:
        str = session.vm.get_gui_status()
        return str
    return ""


@app.route('/asm/vm/src/trace/<trace>', methods=['GET', 'POST'])
def trace_status(trace):
    if request.method == 'POST':
        if trace in ['on', 'off']:
            session.trace = True if trace == 'on' else False
        else:
            session.trace_fn = trace

        return jsonify(session.trace)


@app.route('/asm/vm/src')
def vm():
    # Note, session.cmd needs to be setup as sys.argv would be. For example as: ['as', 'as', 'as1?.s']
    # When initializing VM below, it will read session.cmd as cmd_line and parse accordingly. It will also set
    # working directory according to configuration settings.
    global session
    session = Session()
    cmd = request.args.get('cmd')
    file = request.args.get('file')
    if cmd == "as1":
        session.cmd = [cmd, cmd, file]
    else:  # as2
        # Split file string by space into a list: "/tmp/atm1a /tmp/atm2a /tmp/atm3a" =>
        #   ["/tmp/atm1a", "tmp/atm2a", "/tmp/atm3a"]
        # Then concatenate into one list.
        session.cmd = [cmd, cmd] + file.split(" ")

    print(f"src: {session.cmd}")
    print(f"cwd: {os.getcwd()}")
    session.vm = asm.VM(session.cmd)
    return {'startLine': session.vm.current_lineno(), 'src': session.vm.get_src()}


@app.route('/asm/vm/src/line/<int:line>')
def line(line):
    if line > 0:
        session.vm.exec()
        if session.trace:
            session.vm.dump_trace(trace_fn=session.trace_fn)

    return str(session.vm.current_lineno())


def exec_asm():
    while True:
        if session.goThreadBreak or \
                session.vm.current_lineno() in session.breakLines or \
                session.vm.exit:
            if session.trace:
                session.vm.dump_trace(trace_fn=session.trace_fn)
            break

        session.vm.exec()

    if session.vm.exit:
        session.vm = asm.VM(session.cmd)


@app.route('/asm/vm/src/go')
def go():
    session.goThread = threading.Thread(target=exec_asm)
    session.goThread.start()
    session.goThread.join()

    return str(session.vm.current_lineno())


@app.route('/asm/vm/src/break', methods=['POST'])
def breaking():
    session.logger.info("Breaking")
    session.goThreadBreak = True
    session.goThread.join()
    session.goThreadBreak = False
    return str(session.vm.current_lineno())


@app.route('/asm/vm/brkp/<int:line>', methods=['POST'])
def set_breakpoint(line):
    session.logger.info("Breakpoint @{}".format(str(line)))
    if line in session.breakLines:
        session.breakLines.remove(line)
    else:
        session.breakLines.append(line)

    return str(line)


@app.route('/asm/vm/loglevel/toggle', methods=['POST'])
def log_level():
    session.verbose = not session.verbose
    session.logger.info("Log level verbose: {}".format(session.verbose))
    session.vm.log_level(session.verbose)

    return str(session.verbose)


@sock.route('/asm/vm/log')
def log(sock):
    print("Opening socket log")
    while True:
        log_rec = session.log_queue.get(block=True)
        sock.send(log_rec.getMessage())
        print(f"Log, have sent {log_rec.getMessage()}")
    print("Closing socket log")


if __name__ == '__main__':
    app.run()
