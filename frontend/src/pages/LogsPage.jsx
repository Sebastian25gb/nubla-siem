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
  const { token, logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const fetchLogs = useCallback(async () => {
    try {
      console.log("Token being sent:", token);
      const response = await axios.get(
        `http://127.0.0.1:8000/logs/`, // Eliminamos el parámetro tenant_id
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      console.log("Response from /logs/:", response.data);
      setLogs(response.data);
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
  }, [token, logout, navigate]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  const chartData = logs.map((log) => ({
    timestamp: new Date(log.timestamp).toLocaleTimeString(),
    status: log.status === 'success' ? 1 : log.status === 'failure' ? -1 : 0,
  }));

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
        onClick={fetchLogs}
        style={{ marginLeft: '10px' }}
      >
        Fetch Logs
      </Button>
      <LineChart
        width={600}
        height={300}
        data={chartData}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="timestamp" />
        <YAxis />
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