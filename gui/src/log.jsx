import {useEffect, useState} from 'react';
import './App.css';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import Switch from '@mui/material/Switch';
import FormControlLabel from '@mui/material/FormControlLabel';
import axios from "axios";
import ScrollableFeed from 'react-scrollable-feed';

/*
1) https://github.com/robtaussig/react-use-websocket
2) https://www.npmjs.com/package/react-scrollable-feed
 */

export default function LogWindow() {
    const [logMsg, setLogMsg] = useState([]);
    const {lastMessage} = useWebSocket('ws://127.0.0.1:5000/asm/vm/log');
    const [checked, setChecked] = useState(false);

    useEffect(() => {
        if (lastMessage !== null) {
            setLogMsg((prev) => prev.concat(lastMessage));
        }
    }, [lastMessage, checked, setChecked]);

    const handleChange = (event) => {
        axios
            .post('/asm/vm/loglevel/toggle')
            .then(setChecked(event.target.checked));
    };

    return (
        <>
            <pre className="log">
                <ScrollableFeed>
                    {logMsg.map((message, idx) => (
                        <span key={idx}>{message ? (message.data + "\n") : null}</span>
                    ))}
                </ScrollableFeed>
            </pre>
            <FormControlLabel
                control=
                    {<Switch
                        checked={checked}
                        onChange={handleChange}
                    />}
                label="Verbose logging"
                labelPlacement="start"/>
        </>
    );
}