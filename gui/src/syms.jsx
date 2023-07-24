import {useEffect, useState} from 'react';
import './App.css';
import axios from "axios";
import Paper from '@mui/material/Paper';
import MUIDataTable from "mui-datatables";

export function Labels({cnt}) {
    const [labels, setLabels] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios
            .get("/asm/vm/labels")
            .then((response) => {
                setLabels(response.data);
            })
            .catch((error) => {
                setError(error);
            });

    }, [cnt]);

    if (error) return `Error: ${error?.message}`;

    return (
        <>
            <Paper sx={{width: '100%', overflow: 'hidden'}}>
                <MUIDataTable
                    title={<h2>Labels</h2>}
                    data={labels}
                    columns={["Label", "Address", "Value"]}
                    options={{
                        filter: false, selectableRows: "none", pagination: false,
                        tableBodyHeight: '500px', tableBodyMaxHeight: '500px',
                        print: false, download: false, viewColumns: false,
                        setTableProps: () => {
                            return {padding: 'none', size: 'small'}
                        }
                    }}
                />
            </Paper>
        </>
    );
}

export function Variables({cnt}) {
    const [variables, setVariables] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios
            .get("/asm/vm/variables")
            .then((response) => {
                setVariables(response.data);
            })
            .catch((error) => {
                setError(error);
            });

    }, [cnt]);

    if (error) return `Error: ${error?.message}`;

    return (
        <>
            <Paper sx={{width: '100%', overflow: 'hidden'}}>
                <MUIDataTable
                    title={<h2>Variables</h2>}
                    data={variables}
                    columns={["Variable", "Value"]}
                    options={{
                        filter: false, selectableRows: "none", pagination: false,
                        tableBodyHeight: '500px', tableBodyMaxHeight: '500px',
                        print: false, download: false, viewColumns: false,
                        setTableProps: () => {
                            return {padding: 'none', size: 'small'}
                        }
                    }}
                />
            </Paper>
        </>
    );
}