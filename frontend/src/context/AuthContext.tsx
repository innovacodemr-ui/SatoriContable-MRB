import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { apiClient } from '../services/api';

interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  clientId: string | null;
  clientName: string | null; // Nuevo estado para el nombre de la empresa
  login: (access: string, refresh: string, clientId?: string) => void;
  logout: () => void;
  isLoading: boolean;
  updateClientName: () => Promise<void>; // Función para actualizar nombre tras configurar
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [clientId, setClientId] = useState<string | null>(null);
  const [clientName, setClientName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const navigate = useNavigate();
  const location = useLocation();

  const fetchUser = async () => {
    try {
      const response = await apiClient.get('/auth/me/');
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const updateClientName = async () => {
      try {
          // Intentar obtener el nombre de la empresa actual
          // Si endpoint falla porque no hay empresa, esto captura el error calladamente
          const response = await apiClient.get('/tenants/clients/current/');
          if (response.data && response.data.name) {
              setClientName(response.data.name);
          }
      } catch (err) {
          console.log("No se pudo obtener nombre de empresa (posiblemente no creada aun)");
      }
  };

  useEffect(() => {
    const initAuth = async () => {
      // Check local storage on mount
      const access = localStorage.getItem('access_token');
      const storedClientId = localStorage.getItem('client_id');

      if (access) {
        setIsAuthenticated(true);
        setClientId(storedClientId);
        await fetchUser();
        // Cargar nombre de empresa si hay cliente
        if (storedClientId) {
            await updateClientName();
        }
      }

      // Check for callback params
      if (location.pathname === '/auth/callback') {
        const params = new URLSearchParams(location.search);
        const accessParam = params.get('access');
        const refreshParam = params.get('refresh');
        const clientIdParam = params.get('clientId');

        if (accessParam && refreshParam) {
          login(accessParam, refreshParam, clientIdParam || undefined);
        }
      }

      setIsLoading(false);
    };

    initAuth();
  }, [location]);

  const login = async (access: string, refresh: string, newClientId?: string) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);

    let currentClientId = newClientId || localStorage.getItem('client_id');

    if (newClientId) {
      localStorage.setItem('client_id', newClientId);
      setClientId(newClientId);
      currentClientId = newClientId;
    }

    setIsAuthenticated(true);
    await fetchUser(); // Ensure user data is loaded
    await updateClientName();

    // Redirect logic
    if (!currentClientId || currentClientId === 'undefined' || currentClientId === '') {
      console.warn('No Client ID found during login, redirecting to Setup');
      navigate('/setup');
    } else {
      navigate('/');
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('client_id');
    setIsAuthenticated(false);
    setClientId(null);
    setClientName(null);
    setUser(null);
    navigate('/login');
  };

  return (
    <AuthContext.Provider value={{ 
        isAuthenticated, 
        user, 
        clientId, 
        clientName,
        login, 
        logout, 
        isLoading,
        updateClientName 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
