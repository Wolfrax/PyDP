from flask import Flask, request, jsonify
import asm
import glob
import threading
import queue
import logging
from logging.handlers import QueueHandler
from flask_sock import Sock


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
        self.trace = True
        self.trace_fn = 'trace.txt'
        self.verbose = False

        self.logger = logging.getLogger('pyPDP')

        self.log_queue = queue.Queue(-1)  # Infinite size
        fmt = logging.Formatter('%(asctime)s - %(message)s')

        queue_handler = QueueHandler(self.log_queue)
        queue_handler.setFormatter(fmt)

        self.logger.addHandler(queue_handler)

        self.logger.info('New session')


session = Session()


@app.route('/asm/vm/PSW')
def PSW():
    return jsonify(session.vm.PSW.get())


@app.route('/asm/vm/registers')
def registers():
    return jsonify(session.vm.register)


@app.route('/asm/vm/stack')
def stack():
    return jsonify(list(zip(session.vm.stack_read(), session.vm.stack_read_addr())))


@app.route('/asm/vm/symbols')
def symbols():
    lbls = {}
    for key, addr in session.vm.named_labels.table.items():
        val = session.vm.mem.read(addr, 2)
        lbls[key] = [str(addr).zfill(4), hex(val)]
    syms = {'vars': dict(session.vm.variables.table), 'lbls': lbls}
    return jsonify(syms)


@app.route('/asm/vm/sysstatus')
def sysstatus():
    str = session.vm.get_sys_status()
    return str


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
    fnList = sorted(glob.glob(request.args.get('file')))
    session.cmd = request.args.get('cmd') + ' ' + ''.join(elem + ' ' for elem in fnList)
    session.vm = asm.VM(session.cmd)
    return session.vm.get_src()


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
    while True:
        log_rec = session.log_queue.get(block=True)
        sock.send(log_rec.getMessage())


if __name__ == '__main__':
    app.run()
