// /root/nubla-siem/frontend/src/components/LoginPage.jsx
import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

// Componente para el formulario de login
const LoginPage = () => {
    // Obtener la función login del contexto
    const { login } = useContext(AuthContext);
    // Estados para los campos del formulario
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    // Estado para errores de autenticación
    const [error, setError] = useState(null);
    // Hook para navegación
    const navigate = useNavigate();

    // Manejar el envío del formulario
    const handleSubmit = async (e) => {
        e.preventDefault(); // Prevenir recarga de página
        const success = await login(username, password);
        if (success) {
            navigate('/'); // Redirigir al dashboard
        } else {
            setError('Invalid credentials');
        }
    };

    return (
        <div className="container mx-auto p-4 max-w-md">
            <h2 className="text-2xl font-bold mb-4">Login</h2>
            {error && <div className="text-red-500 mb-4">{error}</div>}
            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium">Username</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="w-full p-2 border rounded"
                        required
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium">Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full p-2 border rounded"
                        required
                    />
                </div>
                <button type="submit" className="w-full bg-blue-500 text-white p-2 rounded">
                    Login
                </button>
            </form>
        </div>
    );
};

export default LoginPage;