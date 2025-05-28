import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';
import { Container, Typography, Button, Box } from '@mui/material';

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
      <Box sx={{ mt: 2 }}>
        <Button
          variant="contained"
          color="primary"
          component={Link}
          to="/mfa-setup"
          sx={{ mr: 2 }}
        >
          Setup MFA
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={handleViewLogs}
          sx={{ mr: 2 }}
        >
          View Logs
        </Button>
        <Button
          variant="contained"
          color="secondary"
          component={Link}
          to="/users"
          sx={{ mr: 2 }}
        >
          Manage Users
        </Button>
        <Button
          variant="contained"
          color="secondary"
          onClick={handleLogout}
        >
          Logout
        </Button>
      </Box>
    </Container>
  );
};

export default DashboardPage;