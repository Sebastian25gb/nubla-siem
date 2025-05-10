import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Container, Typography, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const { logout } = useContext(AuthContext);
  const navigate = useNavigate();

  return (
    <Container>
      <Typography variant="h4" gutterBottom>
        Nubla SIEM Dashboard
      </Typography>
      <Button variant="contained" color="primary" onClick={() => navigate('/logs')}>
        View Logs
      </Button>
      <Button
        variant="outlined"
        color="secondary"
        onClick={logout}
        style={{ marginLeft: '10px' }}
      >
        Logout
      </Button>
    </Container>
  );
};

export default DashboardPage;