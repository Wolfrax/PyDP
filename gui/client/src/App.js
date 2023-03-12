import React, {useState, useEffect} from 'react';
// import React from 'react'
import Button from 'react-bootstrap/Button';
import Stack from 'react-bootstrap/Stack'
import ListGroup from "react-bootstrap/ListGroup";
import ListGroupItem from "react-bootstrap/ListGroupItem";
import Alert from "react-bootstrap/Alert";
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import {Container} from "react-bootstrap";

/*

The UI React app is structured in React components this way:
    * PDPConsole
        * SrcWindow
            * SrcRows
                * SrcIndex: Show line numbers (index), possible to click => highlight
                * SrcLine: Show source code lines, possible to step => highlight
            * Symbols: Show symbol table (variables and named labels)
                * SymVar: Show variables
                    * SymKey: Show key
                    * SymVal: Show value
                * SymLbl: Show labels
                    * SymKey: Show key
                    * SymVal: Show value
            * VMStack: Show stack (address value)
            * StepButton
            * GoButton
            * Register
            * PSW
            * SysStatus

When SrcWind is mounted in the DOM, an ajax-call is made to Flask server to retrieve the source code, the source code
is split on newlines into an array of source code lines.

When a SrcIndex is clicked, the value of the SrcIndex is POST:ed to the server. When the server responds the index
clicked is scrolled into view (centered with a smooth scroll) and highlighted.

When the Step-button is clicked, a callback is made to SrcWindow with a line number retrieved from the server.
This line number is the next line to be executed and is propagated downwards to the SrcLine component.
The SrcLine sets the state (isNextLine) through 'getDerivedStateFromProps', meaning that a props affect the state,
which is rare this to do according to React documentation. Following on that React calls  'componentDidUpdate' which
checks the state flag 'isNextLine', if true the line is scrolled into view. Finally SrcLine 'render' is called by React
which will highlight the line with 'isNextLine' state set to true, other lines are not highlighted.

 */

class SrcIndex extends React.Component {
    constructor(props) {
        super(props);
        this.srcIndexRef = React.createRef();
        this.state = {
            isClicked: false,
        };
        this.handleClick = this.handleClick.bind(this);
        this.executeScroll = this.executeScroll.bind(this);
    }

    executeScroll() {
        this.srcIndexRef.current.scrollIntoView({behavior: "smooth", block: "center"});
    }

    handleClick(e) {
        e.preventDefault();

        fetch("/asm/vm/brkp/" + this.props.index, {
            method: 'POST'
        })
            .then((response) => response.text())
            .then(() => {
                this.executeScroll();
                this.setState({isClicked: !this.state.isClicked});
            });
    }

    render() {
        return this.state.isClicked
            ?
            <button ref={this.srcIndexRef} onClick={this.handleClick} className="idx idxMarked button">
                {this.props.index}
            </button>
            :
            <button ref={this.srcIndexRef} onClick={this.handleClick} className="idx button">
                {this.props.index}
            </button>
    }
}

class SrcLine extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            isNextLine: false,
        };
        this.srcLineRef = React.createRef();
    }

    static getDerivedStateFromProps(props, state) {
        return {isNextLine: props.nextLine === props.index}
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.isNextLine) {
            this.srcLineRef.current.scrollIntoView({behavior: "smooth", block: "center", inline: "start"});
        }
    }

    render() {
        return this.state.isNextLine
            ?
            <div ref={this.srcLineRef} className="src srcMarked">
                {this.props.line}
            </div>
            :
            <div ref={this.srcLineRef} className="src">
                {this.props.line}
            </div>
    }
}

class Registers extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            isLoaded: false,
            curLine: 0,
            update: false,
            registers: "",
        };

        this.get = this.get.bind(this);
        this.RegRef = React.createRef();
    }

    static getDerivedStateFromProps(props, state) {
        return {
            update: props.nextLine !== state.curLine,
            curLine: props.nextLine,
        }
    }

    get() {
        fetch("/asm/vm/registers")
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        registers: result,
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error: error,
                    });
                }
            )
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.update) {
            this.get();
        }
    }

    componentDidMount() {
        this.get();
    }

    render() {
        const items = Object.entries(this.state.registers).map(([key, value]) =>
            <div key={key}>
                <ListGroupItem variant="dark">
                    {key}
                </ListGroupItem>
                <ListGroupItem>
                    {value}
                </ListGroupItem>
            </div>
        );
        return (
            <ListGroup horizontal>
                {items}
            </ListGroup>);
    }
}

class PSW extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            isLoaded: false,
            curLine: 0,
            update: false,
            psw: "",
        };

        this.get = this.get.bind(this);
    }

    static getDerivedStateFromProps(props, state) {
        return {
            update: props.nextLine !== state.curLine,
            curLine: props.nextLine,
        }
    }

    get() {
        fetch("/asm/vm/PSW")
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        psw: result,
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error: error,
                    });
                }
            )
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.update) {
            this.get();
        }
    }

    componentDidMount() {
        this.get();
    }

    render() {
        const items = Object.entries(this.state.psw).map(([key, value]) =>
            <div key={key}>
                <ListGroupItem variant="dark">
                    {key}
                </ListGroupItem>
                <ListGroupItem>
                    {value}
                </ListGroupItem>
            </div>
        );
        return (
            <ListGroup horizontal>
                {items}
            </ListGroup>);
    }
}

class SymVar extends React.Component {
    render() {
        const items = Object.entries(this.props.vars).map(([key, value]) =>
            <div key={key}>
                <div className="sym">{key}</div>
                <div className="sym eq">=</div>
                <div className="src">&nbsp;{value}&nbsp;</div>
            </div>
        );
        return (items);
    }
}

class SymLbl extends React.Component {
    render() {
        const items = Object.entries(this.props.lbls).map(([key, value]) =>
            <div key={key}>
                <div className="sym">{key}</div>
                <div className="sym">[{value[0]}]:&nbsp;</div>
                <div className="src">{value[1]}&nbsp;</div>
            </div>
        );
        return (items);
    }
}

class Symbols extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            isLoaded: false,
            curLine: 0,
            update: false,
            symbols: "",
        };
        this.get = this.get.bind(this);
    }

    get() {
        fetch("/asm/vm/symbols")
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        symbols: result,
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error: error,
                    });
                }
            )
    }

    static getDerivedStateFromProps(props, state) {
        return {
            update: props.nextLine !== state.curLine,
            curLine: props.nextLine,
        }
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.update) {
            this.get();
        }
    }

    componentDidMount() {
        this.get();
    }

    render() {
        const {error, isLoaded} = this.state;

        if (error) {
            return <div>{error.message}</div>;
        } else if (!isLoaded) {
            return <div>...</div>;
        } else {
            return (
                <div>
                    <pre className="pre sympre">
                        <h5 className="symhead">Variables</h5>
                        <SymVar vars={this.state.symbols.vars}/>
                        <br/>
                        <h5 className="symhead">Labels</h5>
                        <SymLbl lbls={this.state.symbols.lbls}/>
                    </pre>
                </div>
            );
        }
    }
}

class VMStack extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            isLoaded: false,
            curLine: 0,
            update: false,
            stack: "",
        };
        this.get = this.get.bind(this);
    }

    static getDerivedStateFromProps(props, state) {
        return {
            update: props.nextLine !== state.curLine,
            curLine: props.nextLine,
        }
    }

    get() {
        fetch("/asm/vm/stack")
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        stack: result,
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error: error,
                    });
                }
            )
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.update) {
            this.get();
        }
    }

    componentDidMount() {
        this.get();
    }

    render() {
        const {error, isLoaded} = this.state;

        if (error) {
            return <div>{error.message}</div>;
        } else if (!isLoaded) {
            return <div>...</div>;
        } else {
            const items = this.state.stack.map((val, index) =>
                <div key={index}>
                    <div className="sym">
                        [{val[1]}]
                    </div>
                    <div className="src">
                        : {val[0]}&nbsp;
                    </div>
                </div>
            );

            return (
                <pre className="pre stackpre">
                    {items}
                </pre>);
        }
    }
}

class SysStatus extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            isLoaded: false,
            curLine: 0,
            update: false,
            status: "",
        };
        this.get = this.get.bind(this);
    }

    static getDerivedStateFromProps(props, state) {
        return {
            update: props.nextLine !== state.curLine,
            curLine: props.nextLine,
        }
    }

    get() {
        fetch("/asm/vm/sysstatus")
            .then(res => res.text())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        status: result,
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error: error,
                    });
                }
            )
    }

    componentDidUpdate(prevProps, prevState) {
        if (this.state.update) {
            this.get();
        }
    }

    componentDidMount() {
        this.get();
    }

    render() {
        return (
            <Alert variant='dark'>
                {this.state.status}
            </Alert>);
    }
}

class SrcRows extends React.Component {
    render() {
        const items = this.props.rows.map((srcLine, index) =>
            <div key={index}>
                <SrcIndex index={index + 1}/>
                <SrcLine line={srcLine} nextLine={this.props.lineNo} index={index + 1}/>
            </div>
        );

        return (
            <pre className="pre">
                {items}
            </pre>);
    }
}

class StepButton extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            lineNo: 0,
            isLoaded: false,
        };
        this.get = this.get.bind(this);
        this.handleClick = this.handleClick.bind(this);
    }

    static getDerivedStateFromProps(props, state) {
        return {
            lineNo: props.nextLine,
        }
    }

    get() {
        fetch("/asm/vm/src/line/" + this.state.lineNo)
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        lineNo: result,
                    });
                    this.props.onNextLineChange(result);
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            )
    }

    handleClick() {
        this.get();
    }

    componentDidMount() {
        this.get();
    }

    render() {
        const {error, isLoaded} = this.state;

        if (error) {
            return <div>{error.message}</div>;
        } else if (!isLoaded) {
            return <div>...</div>;
        } else {
            return (
                <Button onClick={this.handleClick} variant="secondary">Step {this.state.lineNo}</Button>
            );
        }
    }
}

class GoButton extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            error: null,
            lineNo: 0,
            isLoaded: true,
        };
        this.handleGoClick = this.handleGoClick.bind(this);
        this.handleExecClick = this.handleExecClick.bind(this);
    }

    handleGoClick() {
        this.setState({isLoaded: false});

        fetch("/asm/vm/src/go")
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        lineNo: parseInt(result),
                    });
                    this.props.onNextLineChange(this.state.lineNo);
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            )
    }

    handleExecClick() {
        this.setState({isLoaded: true});

        fetch("/asm/vm/src/break", {
            method: 'POST'
        })
            .then(res => res.json())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        lineNo: parseInt(result),
                    });
                    this.props.onNextLineChange(this.state.lineNo);
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            )
    }

    render() {
        const {error, isLoaded} = this.state;

        if (error) {
            return <div>{error.message}</div>;
        } else if (!isLoaded) {
            return (
                <Button onClick={this.handleExecClick} variant="danger">Executing...</Button>
            );
        } else {
            return (
                <Button onClick={this.handleGoClick} variant="secondary">Go</Button>
            );
        }
    }
}

function Trace() {
    const [traceOn, setTrace] = useState(false);

    function onChangeValue(event) {
        const onOff = !traceOn ? 'on' : 'off'
        setTrace(!traceOn);
        fetch("/asm/vm/src/trace/" + onOff, {
            method: 'POST'
        })
    }

    return (
        <div onChange={onChangeValue}>
            <input type="checkbox" value={traceOn}/>&nbsp;Trace
        </div>
    );
}

class TraceFile extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            name: "trace.txt",
        }

        this.handleSubmit = this.handleSubmit.bind(this);
    }

    handleSubmit(event) {
        event.preventDefault();

        fetch("/asm/vm/src/trace/" + this.state.name, {
            method: 'POST'
        })
    }

    render() {
        return (
            <form className="col-sm-12" onSubmit={this.handleSubmit}>
                <label>Trace file:&nbsp;&nbsp;
                    <input
                        type="text"
                        value={this.state.name}
                        onChange={(e) => this.setState({name: e.target.value})}
                    />
                </label>
                <input type="submit" value="Set"/>
            </form>
        );
    }
}

function Log() {
    const [log, setLog] = useState([]);

    useEffect(() => {
        const ws = new WebSocket('ws://127.0.0.1:5000/asm/vm/log');

        ws.onmessage = function (event) {
            try {
                setLog(log => [...log, event.data]);
            } catch (err) {
                console.log(err);
            }
        };
        return () => ws.close();
    }, []);

    return (
    <div>
        <pre className="p-5 mb-4 bg-light rounded-3 log">
            {log.map((e, ind) => <div key={ind}>{e}</div>)}
        </pre>
    </div>);
}

function LogLevel() {
    const [logLevel, setLogLevel] = useState(false);

    function onChangeValue(event) {
        setLogLevel(!logLevel);
        fetch("/asm/vm/loglevel/toggle", {
            method: 'POST'
        })
    }

    return (
        <div onChange={onChangeValue}>
            <input type="checkbox" value={logLevel}/>&nbsp;Verbose logging
        </div>
    );
}

class SrcWindow extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            isLoaded: false,
            txt: "",
            nextLine: 0,
        };
        this.handleNextLineChange = this.handleNextLineChange.bind(this);
    }

    handleNextLineChange(nextLine) {
        this.setState({
            nextLine: nextLine,
        });
    }

    componentDidMount() {
        fetch("/asm/vm/src?" + new URLSearchParams({
            cmd: "as",
            file: this.props.src,
        }))
            .then(res => res.text())
            .then((result) => {
                    this.setState({
                        isLoaded: true,
                        txt: result.split("\n"),
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            )
    }

    render() {
        const {error, isLoaded} = this.state;
        if (error) {
            return <div>Error: {error.message}</div>;
        } else if (!isLoaded) {
            return <div>Loading...</div>;
        } else {
            return (
                <div>
                    <Stack direction="horizontal" className="col-md-8" gap={2}>
                        <Stack>
                            <h5>as {this.props.src}</h5>
                            <SrcRows rows={this.state.txt} lineNo={this.state.nextLine}/>
                        </Stack>
                        <Stack>
                            <h5>Stack</h5>
                            <VMStack nextLine={this.state.nextLine}/>
                        </Stack>
                        <Stack>
                            <h5>Symbols</h5>
                            <Symbols nextLine={this.state.nextLine}/>
                        </Stack>
                        <Stack>
                            <h5>Registers</h5>
                            <Registers nextLine={this.state.nextLine}/>
                            <h5>Processor Status</h5>
                            <PSW nextLine={this.state.nextLine}/>
                            <h5>System Status</h5>
                            <SysStatus nextLine={this.state.nextLine}/>
                            <LogLevel/>
                            <Trace/>
                            <TraceFile/>
                        </Stack>
                    </Stack>

                    <Stack direction="horizontal" gap={2}>
                        <StepButton nextLine={this.state.nextLine} onNextLineChange={this.handleNextLineChange}/>
                        <GoButton onNextLineChange={this.handleNextLineChange}/>
                    </Stack>

                    <hr/>

                    <Stack direction="horizontal" gap={2}>
                        <Log/>
                    </Stack>
                </div>
            );
        }
    }
}


function PDPConsole(props) {
    return (
        <SrcWindow src={props.src}/>
    );
}

function App() {
    const [src, setSrc] = useState("");
    const [loadConsole, setLoadConsole] = useState(false);

    const handleSubmit = (event) => {
        event.preventDefault();
        setSrc(src);
        setLoadConsole(true);
    }

    if (loadConsole) {
        return (
            <div className="App">
                <Container fluid className="p-5 mb-4 bg-light rounded-3">
                    <PDPConsole src={src}/>
                </Container>
            </div>
        );
    }
    else {
        return (
            <div className="App">
                <Container fluid className="p-5 mb-4 bg-light rounded-3">
                    <h2>PDP 11/40 ASM Console</h2>
                    <form onSubmit={handleSubmit}>
                        <label>e.g. as1?.s&nbsp;&nbsp;</label>
                        <input type="text" value={src}
                               onChange={(e) => setSrc(e.target.value)}/>
                        <input type="submit" value="Load"/>
                    </form>
                </Container>
            </div>
        );
    }
}

export default App;
