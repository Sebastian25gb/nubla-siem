// /root/nubla-siem/frontend/src/components/LogsPage.jsx
import React, { useContext, useEffect, useState } from 'react';
import { AuthContext } from '../context/AuthContext';
import useApi from '../hooks/useApi';
import { useNavigate } from 'react-router-dom';

// Componente para mostrar logs filtrados por tenant
const LogsPage = () => {
    // Obtener user y tenantId del contexto de autenticación
    const { tenantId, user } = useContext(AuthContext);
    // Hook personalizado para solicitudes HTTP
    const { request, loading, error } = useApi();
    // Estado para almacenar los logs
    const [logs, setLogs] = useState([]);
    // Hook para navegación
    const navigate = useNavigate();

    // useEffect: Obtener logs al montar el componente
    useEffect(() => {
        // Redirigir a login si no hay usuario autenticado
        if (!user) {
            navigate('/login');
            return;
        }

        // Función asíncrona para obtener logs
        const fetchLogs = async () => {
            try {
                const data = await request('get', '/logs');
                setLogs(data.logs);
            } catch (err) {
                console.error('Error fetching logs:', err);
            }
        };
        fetchLogs();
    }, [user, navigate, request]); // Dependencias: re-ejecutar si cambian

    // Mostrar estado de carga
    if (loading) return <div className="text-center mt-10">Loading...</div>;
    // Mostrar error si ocurre
    if (error) return <div className="text-red-500 text-center mt-10">{error}</div>;

    // Renderizar lista de logs
    return (
        <div className="container mx-auto p-4">
            <h2 className="text-2xl font-bold mb-4">Logs for Tenant {tenantId}</h2>
            <ul className="space-y-2">
                {logs.map((log, index) => (
                    <li key={index} className="p-2 bg-gray-100 rounded">
                        {log.message}
                        <span className="text-sm text-gray-500 ml-2">
                            ({new Date(log.time * 1000).toLocaleString()})
                        </span>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default LogsPage;