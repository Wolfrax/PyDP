import './App.css'
import AsmWindow from "./asm.jsx";
import LogWindow from "./log.jsx";

import * as React from 'react';
import {styled} from '@mui/material/styles';
import Box from '@mui/material/Box';
import Paper from '@mui/material/Paper';
import Grid from '@mui/material/Grid';
import TextField from "@mui/material/TextField";
import MenuItem from "@mui/material/MenuItem";
import {useEffect, useState} from "react";
import {Variables, Labels} from "./syms.jsx";
import {Stack} from "./stack.jsx";
import {Registers, PSW, SysStatus} from "./status.jsx";

const Item = styled(Paper)(({theme}) => ({
    backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
    ...theme.typography.body2,
    padding: theme.spacing(1),
    textAlign: 'center',
    color: theme.palette.text.secondary,
}));

function SelectAsmPass({cmd, onChange}) {
    return (
        <div>
            <Box
                component="form"
                sx={{
                    '& > :not(style)': {m: 1, width: '25ch'},
                }}
                noValidate
                autoComplete="off"
            >
                <h3><u>Asm pass</u></h3>
                <TextField
                    id="outlined-select-asm"
                    select
                    label="Select"
                    defaultValue={cmd}
                    size="small"
                    variant="outlined"
                    style={{backgroundColor: "white"}}
                    onChange={onChange}
                >
                    {['as', 'as2'].map((pass) => (
                        <MenuItem key={pass} value={pass}>{pass}</MenuItem>
                    ))}
                </TextField>
            </Box>
        </div>
    )
}

function App() {
    const [asmFile, setAsmFile] = useState("as1?.s");
    const [asmCmd, setAsmCmd] = useState("as");
    const [cnt, setCnt] = useState(0);
    const [asmLoaded, setAsmLoaded] = useState(0);

    const handleAsmPass = event => {
        if (event.target.value === "as") {
            setAsmFile("as1?.s");
            setAsmCmd("as");
        } else {
            setAsmFile("/tmp/atm1? /tmp/atm2? /tmp/atm3?");
            setAsmCmd("as2");
        }
    }

    const handleAsmLoaded = loaded => {
        setAsmLoaded(loaded);
    }

    const handleAsmUpdate = update => {
        setCnt(cnt => cnt + 1) // update state to force render
    }

    // Note, key-attribute is used for Box-component below, setting this to the value of asmCmd will
    // retrigger the entire tree with Box as root. So when changing between "as" and "as2" (or vice versa)
    // we will reset all and read in new source-code, stack, labels and variables. Note that also LogWindow is reset.
    // For Stack, Labels, Variables we use a cnt-attribute. Cnt is a counter that is stepped when Step/Go-buttons
    // are clicked in AsmWindow, the callback handleAsmUpdate is used by Step/Go with a boolean value ("update") set
    // to true to update cnt. Then cnt is used for Stack, Labels, Variables to update these components with new
    // values as they might change due to execution.

    return (
        <Box key={asmCmd} sx={{width: '100%'}}>
            <Grid container spacing={1}>
                <Grid item xl={2}>
                    <Box display="flex" justifyContent="row">
                        <SelectAsmPass cmd={asmCmd} onChange={handleAsmPass}/>
                    </Box>
                </Grid>
                <Grid item xl={3}>
                    {asmLoaded ? (
                        <Box display="flex" justifyContent="row">
                            <Registers cnt={cnt}/>
                        </Box>
                        ) :
                        <div>Loading...</div>}
                </Grid>
                <Grid item xl={2}>
                    {asmLoaded ? (
                        <Box display="flex" justifyContent="row">
                            <PSW cnt={cnt}/>
                        </Box>
                        ) :
                        <div>Loading...</div>}
                </Grid>
                <Grid item xl={5}>
                    <Box display="flex" justifyContent="row">
                        {asmLoaded ? <SysStatus cnt={cnt}/> : <div>Loading...</div>}
                    </Box>
                </Grid>
                <Grid item xl={5}>
                    {asmCmd === "as" ? (
                            <Item><AsmWindow cmd={asmCmd} file={asmFile} onLoaded={handleAsmLoaded}
                                             onUpdate={handleAsmUpdate}/></Item>
                        ) : (
                            <Item><AsmWindow cmd={asmCmd} file={asmFile}  onLoaded={handleAsmLoaded}
                                             onUpdate={handleAsmUpdate}/></Item>
                        )}
                </Grid>
                <Grid item xl={2}>
                    {asmLoaded ? <Item><Stack cnt={cnt}/></Item> : <div>Loading...</div>}
                </Grid>
                <Grid item xl={3}>
                    {asmLoaded ? <Item><Labels cnt={cnt}/></Item> : <div>Loading...</div>}
                </Grid>
                <Grid item xl={2}>
                    {asmLoaded ? <Item><Variables cnt={cnt}/></Item> : <div>Loading</div>}
                </Grid>
                <Grid item xl={12}>
                    <Item><LogWindow/></Item>
                </Grid>
            </Grid>
        </Box>
    );
}

export default App
