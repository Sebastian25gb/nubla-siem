// /root/nubla-siem/frontend/src/components/Dashboard.jsx
import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

// Componente principal del dashboard
const Dashboard = () => {
    // Obtener user, tenantId y logout del contexto
    const { user, tenantId, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    // Redirigir a login si no hay usuario autenticado
    if (!user) {
        navigate('/login');
        return null;
    }

    return (
        <div className="container mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
            <p>Welcome, {user.username} (Tenant: {tenantId})</p>
            <div className="space-x-4 mt-4">
                <button
                    onClick={() => navigate('/logs')}
                    className="bg-blue-500 text-white p-2 rounded"
                >
                    View Logs
                </button>
                <button
                    onClick={() => navigate('/user')}
                    className="bg-blue-500 text-white p-2 rounded"
                >
                    User Profile
                </button>
                <button
                    onClick={() => navigate('/mfa-setup')}
                    className="bg-blue-500 text-white p-2 rounded"
                >
                    Setup MFA
                </button>
                <button
                    onClick={logout}
                    className="bg-red-500 text-white p-2 rounded"
                >
                    Logout
                </button>
            </div>
        </div>
    );
};

export default Dashboard;