//'use strict';
import React, { useRef } from 'react'

const e = React.createElement;

class SrcIndex extends React.Component  {
    constructor(props) {
        super(props);
        this.myRef = React.createRef();
        this.state = {
            isClicked: false,
        };
        this.handleClick = this.handleClick.bind(this);
        this.executeScroll = this.executeScroll.bind(this);
    }

    executeScroll() {
        this.myRef.current.scrollIntoView({behavior: "smooth", block: "center"});
    }

    handleClick(e) {
        e.preventDefault();

        fetch("http://127.0.0.1:5000/asm_src", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({id: this.props.index})
        })
            .then((response) => response.json())
            .then((data) => {
                this.executeScroll();
                this.setState({isClicked: !this.state.isClicked});
                console.log(data);
            });
    }

    render() {
        return this.state.isClicked
            ? <button ref={this.myRef} onClick={this.handleClick} className="idxMarked button">{this.props.index}: </button>
            : <button ref={this.myRef} onClick={this.handleClick} className="idx button">{this.props.index}: </button>
    }
}

class SrcLine extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            lineIndex: 0,
            isNextLine: false,
        };

        this.myRef = React.createRef();
        this.handleScroll = this.handleScroll.bind(this);
        this.executeScroll = this.executeScroll.bind(this);
    }

    handleScroll() {
        this.setState()
        this.myRef.current.scrollIntoView({behavior: "smooth", block: "center"});
    }

    executeScroll() {
        this.myRef.current.scrollIntoView({behavior: "smooth", block: "center"});
    }

    render() {
        if (this.props.index === this.props.lineNo) {
            this.executeScroll();
            return <div className="srcMarked">{this.props.line}</div>
        }
        else {
            return <div className="src">{this.props.line}</div>
        }
    }
}

class SrcRows extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            lineNo: props.lineNo,
        };
    }

    render() {
        const items = this.props.rows.map((srcLine, index) =>
            <div key={index}>
                <SrcIndex index={index}/>
                <SrcLine line={srcLine} lineNo={this.props.lineNo} index={index}/>
            </div>)

        return (items);
    }
}

class SrcWindow extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            error: null,
            lineNo: props.nextLine,
            isLoaded: false,
            txt: ""
        };
    }

    componentDidMount() {
        fetch("http://127.0.0.1:5000/asm_src")
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
        const {error, isLoaded, txt} = this.state;
        if (error) {
            return <div>Error: {error.message}</div>;
        } else if (!isLoaded) {
            return <div>Loading...</div>;
        } else {
            console.log("SrcWindow render, lineNo: " + this.props.nextLine)
            return (
                <pre>
                    <SrcRows rows={this.state.txt} lineNo={this.props.nextLine}/>
                </pre>
            );
        }
    }

}

class StepButton extends React.Component {
    constructor(props) {
        super(props);
        this.state = {line_no: 0};

        this.handleClick = this.handleClick.bind(this);
    }

  handleClick() {
        fetch("http://127.0.0.1:5000/asm_line")
            .then(res => res.json())
            .then((result) => {
                    this.setState({ line_no: result });
                    this.props.onNextLineChange(result);
                }
            )
  }

    render() {
        return (
            <button onClick={this.handleClick} className="button">Step {this.props.nextLine}</button>
        );
    }
}

class GoButton extends React.Component {
    render() {
        return (
            <button className="button">Go</button>
        );
    }
}

class PDPConsole extends React.Component {
    constructor() {
        super();
        this.state = {
            nextLine: 1
        };

        this.handleNextLineChange = this.handleNextLineChange.bind(this);
    }

    handleNextLineChange(nextLine) {
        this.setState({
            nextLine: nextLine
        });
        console.log("PDPConsole: handleNextLineChange " + nextLine);
    }

    render() {
        return (
            <div>
                <SrcWindow onNextLineChange={this.handleNextLineChange} nextLine={this.state.nextLine}/>
                <StepButton onNextLineChange={this.handleNextLineChange} nextLine={this.state.nextLine}/>
                <GoButton/>
            </div>
        );
    }
}

const domContainer = document.querySelector('#asm_src_container');
ReactDOM.render(e(PDPConsole), domContainer);

