// /root/nubla-siem/frontend/src/hooks/useApi.js
import { useState, useCallback } from 'react';
import axios from 'axios';

// Hook personalizado para manejar solicitudes HTTP
const useApi = () => {
    // Estado para indicar si la solicitud está en curso
    const [loading, setLoading] = useState(false);
    // Estado para almacenar errores de la solicitud
    const [error, setError] = useState(null);

    // useCallback: Memoriza la función para evitar recrearla en cada render
    const request = useCallback(async (method, url, data = null) => {
        setLoading(true);
        setError(null);
        try {
            // Configuración de la solicitud con axios
            const config = {
                method,
                url: `http://backend:8000${url}`,
                headers: {
                    Authorization: `Bearer ${localStorage.getItem('token')}`, // Incluir token JWT
                },
                data,
            };
            const response = await axios(config);
            setLoading(false);
            return response.data; // Devolver los datos de la respuesta
        } catch (err) {
            // Manejar errores de la solicitud
            setError(err.response?.data?.detail || 'Request failed');
            setLoading(false);
            throw err;
        }
    }, []); // Array vacío: la función no depende de props/state externos

    return { request, loading, error };
};

export default useApi;