import React, { useState, useEffect, useContext, useCallback } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';

const LogsPage = () => {
  const [logs, setLogs] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');
  const [lastTimestamp, setLastTimestamp] = useState(null);
  const { token, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const fetchLogs = useCallback(async (loadMore = false) => {
    try {
      console.log("Token being sent:", token);
      const response = await axios.get(
        `http://107.152.39.90:8000/logs/`,  // Cambia la URL
        {
          headers: { Authorization: `Bearer ${token}` },
          params: loadMore && lastTimestamp ? { before: lastTimestamp } : {},
        }
      );
      console.log("Response from /logs/:", response.data);

      if (loadMore) {
        setLogs((prevLogs) => {
          const newLogs = response.data.filter(
            (newLog) => !prevLogs.some((log) => log.timestamp === newLog.timestamp)
          );
          const updatedLogs = [...prevLogs, ...newLogs];
          return updatedLogs;
        });
      } else {
        setLogs(response.data);
      }

      if (response.data.length > 0) {
        setLastTimestamp(response.data[response.data.length - 1].timestamp);
      }

      setErrorMessage('');
    } catch (err) {
      console.error('Error fetching logs:', err);
      if (err.response && err.response.status === 401) {
        setErrorMessage('Por temas de seguridad se ha cerrado la sesión, por favor ingrese de nuevo');
        logout();
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else if (err.code === 'ERR_NETWORK' || err.message.includes('Network Error')) {
        setErrorMessage('Error de conexión con el servidor. Por favor, intenta de nuevo más tarde.');
        logout();
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        setErrorMessage('Error al obtener los logs. Por favor, intenta de nuevo.');
      }
    }
  }, [token, logout, navigate, lastTimestamp]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const chartData = logs.map((log) => {
    let statusValue;
    if (log.status === 'información') {
      statusValue = 1;
    } else if (log.status && log.status.toLowerCase().includes('error')) {
      statusValue = -1;
    } else if (log.status && log.status.toLowerCase().includes('warning')) {
      statusValue = 0;
    } else {
      statusValue = 0;
    }

    return {
      timestamp: new Date(log.timestamp).toLocaleTimeString(),
      status: statusValue,
    };
  });

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Logs for Tenant
      </Typography>
      {errorMessage && (
        <Typography color="error" gutterBottom>
          {errorMessage}
        </Typography>
      )}
      <Button
        variant="contained"
        onClick={() => fetchLogs(false)}
        style={{ marginLeft: '10px' }}
      >
        Fetch Logs
      </Button>
      <Button
        variant="contained"
        onClick={() => fetchLogs(true)}
        style={{ marginLeft: '10px' }}
        disabled={!lastTimestamp}
      >
        Load More
      </Button>
      <LineChart
        width={600}
        height={300}
        data={chartData}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis domain={[-1, 1]} ticks={[-1, 0, 1]} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="status" stroke="#8884d8" />
      </LineChart>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Timestamp</TableCell>
            <TableCell>Device ID</TableCell>
            <TableCell>User ID</TableCell>
            <TableCell>Action</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Source</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {logs.map((log, index) => (
            <TableRow key={index}>
              <TableCell>{log.timestamp}</TableCell>
              <TableCell>{log.device_id}</TableCell>
              <TableCell>{log.user_id}</TableCell>
              <TableCell>{log.action}</TableCell>
              <TableCell>{log.status}</TableCell>
              <TableCell>{log.source}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Container>
  );
};

export default LogsPage;