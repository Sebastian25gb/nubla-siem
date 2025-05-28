import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { TextField, Button, Container, Typography } from '@mui/material';

const LoginPage = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [mfaCode, setMfaCode] = useState('');
    const [error, setError] = useState('');
    const [mfaRequired, setMfaRequired] = useState(false);
    const [tempToken, setTempToken] = useState('');
    const { login } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const formData = new URLSearchParams();
            formData.append('username', username);
            formData.append('password', password);

            const response = await axios.post('http://107.152.39.90:8000/token/', formData, {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
            });
            if (response.data.mfa_required) {
                setMfaRequired(true);
                setTempToken(response.data.access_token);
            } else {
                login(response.data.access_token);
                navigate('/dashboard');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Error logging in');
        }
    };

    const handleMfaVerify = async (e) => {
        e.preventDefault();
        setError('');
        try {
            const response = await axios.post('http://107.152.39.90:8000/api/verify-mfa', {
                code: mfaCode
            }, {
                headers: { Authorization: `Bearer ${tempToken}` }
            });
            login(response.data.access_token);
            navigate('/dashboard');
        } catch (err) {
            setError(err.response?.data?.detail || 'Error verifying MFA code');
        }
    };

    return (
        <Container maxWidth="sm">
            <Typography variant="h4" gutterBottom>
                Login to Nubla SIEM
            </Typography>
            {error && <Typography color="error">{error}</Typography>}
            {!mfaRequired ? (
                <form onSubmit={handleLogin}>
                    <TextField
                        label="Username"
                        fullWidth
                        margin="normal"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                    <TextField
                        label="Password"
                        type="password"
                        fullWidth
                        margin="normal"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <Button type="submit" variant="contained" color="primary" fullWidth>
                        Login
                    </Button>
                </form>
            ) : (
                <form onSubmit={handleMfaVerify}>
                    <TextField
                        label="MFA Code (from Microsoft Authenticator)"
                        fullWidth
                        margin="normal"
                        value={mfaCode}
                        onChange={(e) => setMfaCode(e.target.value)}
                    />
                    <Button type="submit" variant="contained" color="primary" fullWidth>
                        Verify MFA
                    </Button>
                </form>
            )}
        </Container>
    );
};

export default LoginPage;