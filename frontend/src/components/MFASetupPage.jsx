// /root/nubla-siem/frontend/src/components/MFASetupPage.jsx
import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

// Componente para configurar MFA (esqueleto)
const MFASetupPage = () => {
    const { user } = useContext(AuthContext);
    const navigate = useNavigate();

    // Redirigir a login si no hay usuario autenticado
    if (!user) {
        navigate('/login');
        return null;
    }

    return (
        <div className="container mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">MFA Setup</h2>
            <p>Configure Multi-Factor Authentication for {user.username}</p>
            {/* TODO: Implementar lógica de MFA (por ejemplo, QR code para Google Authenticator) */}
        </div>
    );
};

export default MFASetupPage;