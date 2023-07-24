import {useEffect, useState} from 'react';
import './App.css';
import axios from "axios";
import Paper from '@mui/material/Paper';
import MUIDataTable from "mui-datatables";

export function Stack({cnt}) {
    const [stack, setStack] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        axios
            .get("/asm/vm/stack")
            .then((response) => {
                setStack(response.data);
            })
            .catch((error) => {
                setError(error);
            });

        return () => {
            setStack([]);
        };

    }, [cnt]);

    if (error) return `Error: ${error?.message}`;

    return (
        <>
            <Paper sx={{width: '100%', overflow: 'hidden'}}>
                <MUIDataTable
                    title={<h2>Stack</h2>}
                    data={stack}
                    columns={["Address", "Value"]}
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