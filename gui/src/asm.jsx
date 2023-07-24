import {useEffect, useRef, useState} from 'react';
import Button from '@mui/material/Button';
import ButtonGroup from '@mui/material/ButtonGroup';
import axios from 'axios';
import './App.css';
import FormControlLabel from "@mui/material/FormControlLabel";
import Switch from "@mui/material/Switch";
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import {styled} from "@mui/material/styles";
import Paper from "@mui/material/Paper";

/*
We define "AsmWindow" component here.
This component will fetch assembler (as1?.s or as2?.s) source code and display this using the "<pre>" HTML tag.
This tag is styled in App.css.

AsmWindow have 4 components:
1. Source code lines
2. To the left of the source code, line indexes. These are clickable buttons to set/remove breakpoints
3. A Go-button. Clicking this will start execution of the assembler until done or hitting a breakpoint.
The Go-button will transform into a Break-button while executing. Hitting break will stop execution.
4. A Step-button. This will make a step in the code and executing the next line.
The line to be executed are marked with darkgrey-color.

Step/Go/Break will scroll the source code so that the nextline to be executed are in the middle.

When initiating, the component will fetch source code from the API-server using "/asm/vm/src" URL.
The server will respond with a structure: {startLine: N, src: "..."}, startLine is the first line that can be
executed, src is the assembler source code.
Note that startLine is the line-number for the source code, below we use arrays, where the array-index is an offset,
hence we need to adjust startLine with -1.

We split the received source code on newlines ("\n") and store each row as an array element together with 2 other
attributes:
- id: which is the current index + 1
- inFocus: which is default false. This is used to highlight (in darkgrey) the next line to be executed
We set the value of the state variable asmCode to this array, then we set the state variable lineNo to the value of
startLine - 1. Using state variable will trigger rendering if these variable values are changed.

Go-button is trivial, we simply trigger go to the API server and wait for completion, the server will return next line.

Step-button is slightly more complicated. First we execute the step towards the API server who will respond with the
next line to be executed. When done, we loop through the effect-variable asmCode and when the returned line number is
equal to the index of the source code lines in asmCode we set inFocus to false (this will remove the darkgrey background
when rendering). Then we scroll to the next line to be executed.
When scrolling we need to know which DOM-element to scroll to. This is done through the effect-variable asmLineRef.

Normally, when using effect-variables in React, the variable only contains one reference to a DOM-element, normally
tied to the element where a user interaction took place (like a button that is clicked). In our case, we want to
scroll to the next line to be executed (as returned by the API server), However, we need to know which element.
The trick is by reference one, instead of creating an effect-variable with one element reference, we create asmLineRef
as an array of references to elements, each element is equal to the source code line. Thus, we can use the returned
value from API server as an index into this effect variable. Creating this array is done in the rendering part at the
following statement:

    <div key={srcLine.id} ref={(element) => asmLineRef.current.push(element)}>

ref-attribute is by React and will return the DOM-element which we push into asmLineRef effect-variable.
Note the 'current'-part. React will create an effect-variable as on object:

    {current: DOM-element }

In our case this will be:

    {current: [DOM-element 1, DOM-element 2, ..., DOM-element N}

Note that above statement is part of mapping each element of the asmCode-list, so each element pushed into
asmLineRef will be a unique reference to that specific <div>-element. Neat trick by reference 1.

Note that for AsmIndex, we create a column of buttons to the left of each source code line. The value of the button
is the line number for each source code line. As each button is clickable, we handle this in handleClick function in
the AsmIndex component. Here we can set and unset breakpoints but posting the value (index props) to the API server.
As we 'know' which button is clicked, we can use the asmIndexRef-variable to scroll into view. Here we don't need
the same type of array-solution as described above.

Reference 2 is a particularly good overview of Javascript paradigm used in React.

References:
1) https://mattclaffey.medium.com/adding-react-refs-to-an-array-of-items-96e9a12ab40c
2) https://www.robinwieruch.de/javascript-fundamentals-react-requirements/#shorthand-object-assignment
3) https://blog.miguelgrinberg.com/post/how-to-create-a-react--flask-project
4) https://react.dev/
5) https://vitejs.dev/
6) https://mui.com/
7) https://axios-http.com/

*/

const Item = styled(Paper)(({theme}) => ({
    backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}));

function AsmIndex({index}) {
    const [isClicked, setClicked] = useState(false);
    const asmIndexRef = useRef(null);
    const url = `/asm/vm/brkp/${index}`;

    function handleClick() {
        axios.post(url).then(() => {
            asmIndexRef.current.scrollIntoView({behavior: "smooth", block: "center"});
            setClicked(!isClicked);
        });
    }

    return (
        <>
            {isClicked ? (
                    <button ref={asmIndexRef} onClick={handleClick} className="idx idxMarked button">
                        {index}
                    </button>)
                : (
                    <button ref={asmIndexRef} onClick={handleClick} className="idx button">
                        {index}
                    </button>)}
        </>
    )
}

export default function AsmWindow({cmd, file, onUpdate, onLoaded}) {
    const [asmCode, setAsmCode] = useState([]);
    const [error, setError] = useState(null);
    const [lineNo, setLineNo] = useState(0);
    const [goButton, setGoButton] = useState({text: "Go", active: true})
    const asmLineRef = useRef([]);
    const [traceChecked, setTraceChecked] = useState(false);

    const scroll = (response) => {
        asmCode.map((item, index) => {
            if (item.id === response.data) {
                asmLineRef.current[index].scrollIntoView({behavior: "smooth", block: "center"});
                item.inFocus = true;
            } else {
                item.inFocus = false;
            }
        })
    };

    useEffect(() => {
        axios
            .get("/asm/vm/src", {params: {cmd: cmd, file: file}})
            .then((response) => {
                let asm = [];
                response.data.src.split("\n").map((line, index) => {
                    asm.push({id: index + 1, src: line, inFocus: false});
                });
                asm[response.data.startLine - 1].inFocus = true;
                setAsmCode(asm);
                setLineNo(response.data.startLine - 1);
                scroll({data: response.data.startLine - 1});
                onUpdate(true);
                onLoaded(true);
            })
            .catch((error) => {
                setError(error);
                onUpdate(false);
            });

        return () => {
            onUpdate(false);
        };
    }, [cmd, file]);

    if (error) return `Error: ${error?.message}`;

    function handleGoClick() {
        if (goButton.active) {
            setGoButton({text: "Break", active: false});
            axios
                .get("/asm/vm/src/go")
                .then((response) => {
                    scroll(response);
                    setGoButton({text: "Go", active: true});
                    setLineNo(response.data - 1);
                    onUpdate(true);
                });
        } else {
            axios
                .post("/asm/vm/src/break")
                .then((response) => {
                    scroll(response);
                    setGoButton({text: "Go", active: true});
                    setLineNo(response.data - 1);
                    onUpdate(true);
                });
        }
    }

    function handleStepClick() {
        axios
            .get("/asm/vm/src/line/" + (lineNo + 1))
            .then((response) => {
                scroll(response);
                setLineNo(response.data - 1);
                onUpdate(true);
            });
    }

    const handleTraceChange = (event) => {
        const traceStatus = event.target.checked ? 'on' : 'off'
        axios
            .post("/asm/vm/src/trace/"+ traceStatus)
            .then(setTraceChecked(event.target.checked));
    };

    const handleTraceFilenameChange = (event) => {
        if (event.key === 'Enter') {
            axios
                .post("/asm/vm/src/trace/" + event.target.value)
                .then(response => console.log("Trace filename: " + response.data))
        }
    };

    // Note the usage of "key={srcLine.src} for AsmIndex component below. This will ensure that any set breakpoints
    // are removed if we reload as2 when being at a1 (or vice versa).
    // That is, assume we have loaded the first pass of the assembler ("as1") and set some breakpoints. If we now
    // load "as2" (the second pass part of the assembler), we want to ensure that any previous breakpoint highlights
    // in AsmIndex-component is removed. This is done by using the "key={srcLine.src}" below.
    // Note that if we used "key={srcLine.id} we would not reset breakpoints.
    // For details on how to reset state: https://react.dev/learn/preserving-and-resetting-state
    //

    return (
        <>
            <pre className="pre">
                {asmCode.map(srcLine => (
                    <div key={srcLine.id} ref={(element) => asmLineRef.current.push(element)}>
                        <AsmIndex key={srcLine.src} index={srcLine.id}/>
                        <div className={`${srcLine.inFocus ? "src srcMarked" : "src"}`}>
                            <span style={{backgroundColor: srcLine.inFocus ? "darkgrey" : "rgb(255, 247, 229)"}}>
                                {srcLine.src}
                            </span>
                        </div>
                    </div>
                ))}
            </pre>
            <Box sx={{flexGrow: 1}}>
                <Grid container spacing={2}>
                    <Grid item xs={6}>
                        <ButtonGroup variant="outlined" aria-label="outlined button group">
                            <Button
                                style={{backgroundColor: goButton.active ? "white" : "lightblue"}}
                                onClick={handleGoClick}>
                                {goButton.text}
                            </Button>
                            <Button
                                onClick={handleStepClick}>
                                Step
                            </Button>
                        </ButtonGroup>
                    </Grid>
                    <Grid item xs={2}>
                        <FormControlLabel
                            control={<Switch checked={traceChecked} onChange={handleTraceChange}/>}
                            label="Trace"
                            labelPlacement="start"/>
                    </Grid>
                    <Grid item xs={4}>
                        <TextField label="Trace filename" id="outlined-size-smal" defaultValue="Trace.txt"
                                   variant="outlined" size="small" onKeyPress={handleTraceFilenameChange}/>
                    </Grid>
                </Grid>
            </Box>
        </>
    )
}


