// /root/nubla-siem/frontend/src/components/UserPage.jsx
import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

// Componente para mostrar el perfil del usuario (esqueleto)
const UserPage = () => {
    const { user, tenantId } = useContext(AuthContext);
    const navigate = useNavigate();

    // Redirigir a login si no hay usuario autenticado
    if (!user) {
        navigate('/login');
        return null;
    }

    return (
        <div className="container mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">User Profile</h2>
            <p>Username: {user.username}</p>
            <p>Tenant: {tenantId}</p>
            {/* TODO: Implementar detalles del usuario (por ejemplo, email, fecha de creación) */}
        </div>
    );
};

export default UserPage;