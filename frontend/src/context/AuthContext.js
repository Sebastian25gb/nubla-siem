// /root/nubla-siem/frontend/src/context/AuthContext.js
import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from 'jwt-decode'; // Cambiado a importación nombrada

// Crear un contexto para compartir el estado de autenticación
export const AuthContext = createContext();

// Proveedor del contexto que envuelve la aplicación
export const AuthProvider = ({ children }) => {
    // Estado para el usuario autenticado (username) y tenantId
    const [user, setUser] = useState(null);
    const [tenantId, setTenantId] = useState(null);
    // Estado para indicar si el contexto está cargando
    const [loading, setLoading] = useState(true);

    // useEffect: Verifica si hay un token almacenado al cargar la aplicación
    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                // Decodificar el token JWT para obtener username y tenant_id
                const decoded = jwtDecode(token);
                setUser({ username: decoded.sub });
                setTenantId(decoded.tenant_id);
            } catch (error) {
                console.error('Invalid token:', error);
                localStorage.removeItem('token'); // Eliminar token inválido
            }
        }
        setLoading(false); // Indicar que el contexto está listo
    }, []); // Array vacío: solo se ejecuta al montar

    // Función para iniciar sesión
    const login = async (username, password) => {
        try {
            // Enviar solicitud al endpoint /token del backend
            const response = await axios.post('http://backend:8000/token', {
                username,
                password,
            });
            const token = response.data.access_token;
            localStorage.setItem('token', token); // Guardar token en localStorage
            const decoded = jwtDecode(token);
            setUser({ username: decoded.sub });
            setTenantId(decoded.tenant_id);
            return true; // Login exitoso
        } catch (error) {
            console.error('Login failed:', error);
            return false; // Login fallido
        }
    };

    // Función para cerrar sesión
    const logout = () => {
        localStorage.removeItem('token');
        setUser(null);
        setTenantId(null);
    };

    // Proveer el contexto a los componentes hijos
    return (
        <AuthContext.Provider value={{ user, tenantId, login, logout, loading }}>
            {children}
        </AuthContext.Provider>
    );
};