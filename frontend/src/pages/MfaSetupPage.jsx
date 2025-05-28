import React, { useState, useContext } from 'react';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';
import { Container, Typography, Button, Box } from '@mui/material';

const MfaSetupPage = () => {
    const { token } = useContext(AuthContext);
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [qrCode, setQrCode] = useState('');

    const handleEnableMfa = async () => {
        setMessage('');
        setError('');
        setQrCode('');
        try {
            const response = await axios.post('http://107.152.39.90:8000/api/enable-mfa', {}, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setMessage(response.data.message);
            setQrCode(response.data.qr_code);
        } catch (err) {
            setError(err.response?.data?.detail || 'Error enabling MFA');
        }
    };

    return (
        <Container maxWidth="sm">
            <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Typography variant="h4" gutterBottom>
                    Setup Multi-Factor Authentication
                </Typography>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleEnableMfa}
                    sx={{ mt: 2 }}
                >
                    Enable MFA
                </Button>
                {message && (
                    <Typography color="success.main" sx={{ mt: 2 }}>
                        {message}
                    </Typography>
                )}
                {error && (
                    <Typography color="error" sx={{ mt: 2 }}>
                        {error}
                    </Typography>
                )}
                {qrCode && (
                    <Box sx={{ mt: 2 }}>
                        <Typography>Scan this QR code with Microsoft Authenticator:</Typography>
                        <img src={qrCode} alt="MFA QR Code" style={{ maxWidth: '100%' }} />
                    </Box>
                )}
            </Box>
        </Container>
    );
};

export default MfaSetupPage;