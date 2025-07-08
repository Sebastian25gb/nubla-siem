// /root/nubla-siem/frontend/src/App.jsx
import React, { Suspense } from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import LoginPage from './components/LoginPage';
import LogsPage from './components/LogsPage';
import MFASetupPage from './components/MFASetupPage';
import Register from './components/Register';
import UserPage from './components/UserPage';
import Dashboard from './components/Dashboard';
import './styles/tailwind.css';

// Componente principal de la aplicación
const App = () => {
    return (
        <AuthProvider>
            <Router>
                {/* Suspense: Mostrar fallback mientras se cargan componentes lazy */}
                <Suspense fallback={<div>Loading...</div>}>
                    <Routes>
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/logs" element={<LogsPage />} />
                        <Route path="/mfa-setup" element={<MFASetupPage />} />
                        <Route path="/register" element={<Register />} />
                        <Route path="/user" element={<UserPage />} />
                        <Route path="/" element={<Dashboard />} />
                    </Routes>
                </Suspense>
            </Router>
        </AuthProvider>
    );
};

export default App;