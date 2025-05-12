import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { Container, Typography, Button } from '@mui/material';

const DashboardPage = () => {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleViewLogs = () => {
    navigate('/logs');
  };

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Nubla SIEM Dashboard
      </Typography>
      <Button
        variant="contained"
        color="primary"
        onClick={handleViewLogs}
        style={{ marginRight: '10px' }}
      >
        View Logs
      </Button>
      <Button variant="contained" color="secondary" onClick={handleLogout}>
        Logout
      </Button>
    </Container>
  );
};

export default DashboardPage;