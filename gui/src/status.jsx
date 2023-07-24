import {useEffect, useState} from 'react';
import './App.css';
import axios from "axios";
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

export function Registers({cnt}) {
    const [registers, setRegisters] = useState({});
    const [error, setError] = useState(null);
    const reg_list = ["r0", "r1", "r2", "r3", "r4", "r5", "sp", "pc"];

    useEffect(() => {
        axios
            .get("/asm/vm/registers")
            .then((response) => {
                setRegisters(response.data);
            })
            .catch((error) => {
                setError(error);
            });

        return () => {
            setRegisters({});
        };

    }, [cnt]);

    if (error) return `Error: ${error?.message}`;

    return (
        <>
            <Paper sx={{width: '100%', overflow: 'hidden'}}>
                <h3><b>Registers</b></h3>
                <TableContainer sx={{maxHeight: 500}}>
                    <Table size="small" aria-label="a dense table" stickyHeader>
                        <TableHead>
                            <TableRow>
                                {reg_list.map(e =>
                                    <TableCell key={e} align="left"><b>{e}</b></TableCell>)}
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow sx={{'&:last-child td, &:last-child th': {border: 0}}}>
                                {reg_list.map(e =>
                                    <TableCell key={e} align="left">{registers[e]}</TableCell>)}
                            </TableRow>
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </>
    );
}

export function PSW({cnt}) {
    const [psw, setPSW] = useState({});
    const [error, setError] = useState(null);

    useEffect(() => {
        axios
            .get("/asm/vm/PSW")
            .then((response) => {
                setPSW(response.data);
            })
            .catch((error) => {
                setError(error);
            });

        return () => {
            setPSW({});
        };

    }, [cnt]);

    if (error) return `Error: ${error?.message}`;

    return (
        <>
            <Paper sx={{width: '100%', overflow: 'hidden'}}>
                <h3><b>PSW</b></h3>
                <TableContainer sx={{maxHeight: 500}}>
                    <Table size="small" aria-label="a dense table" stickyHeader>
                        <TableHead>
                            <TableRow>
                                <TableCell align="left"><b>N</b></TableCell>
                                <TableCell align="left"><b>Z</b></TableCell>
                                <TableCell align="left"><b>V</b></TableCell>
                                <TableCell align="left"><b>C</b></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow sx={{'&:last-child td, &:last-child th': {border: 0}}}>
                                <TableCell component="th" scope="row">{psw.N}</TableCell>
                                <TableCell align="left">{psw.Z}</TableCell>
                                <TableCell align="left">{psw.V}</TableCell>
                                <TableCell align="left">{psw.C}</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </TableContainer>
            </Paper>
        </>
    );
}

export function SysStatus({cnt}) {
    const [sysStatus, setSysStatus] = useState("");
    const [error, setError] = useState(null);

    useEffect(() => {
        axios
            .get("/asm/vm/sysstatus")
            .then((response) => {
                setSysStatus(response.data);
            })
            .catch((error) => {
                setError(error);
            });

        return () => {
            setSysStatus("");
        };

    }, [cnt]);

    if (error) return `Error: ${error?.message}`;

    return (
        <>
            <Paper sx={{width: '100%', overflow: 'hidden'}}>
                <h3><b>System Status</b></h3>
                <div>{sysStatus}</div>
            </Paper>
        </>
    );
}
