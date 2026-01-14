import React, { useState } from 'react';
import { Box, Paper, TextField, Button, Typography, Container, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/api';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await authService.login({ username, password });
      navigate('/');
    } catch (err: any) {
      console.error(err);
      setError('Credenciales inválidas. Intente de nuevo.');
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography component="h1" variant="h5" align="center" gutterBottom>
            Satori Contable
          </Typography>
          <Typography variant="body2" align="center" color="textSecondary" gutterBottom>
            Sistema Contable - Cali, Colombia
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
          )}

          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="username"
              label="Usuario"
              name="username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Contraseña"
              type="password"
              id="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              Iniciar Sesión
            </Button>

            <Box sx={{ mt: 2, borderTop: 1, borderColor: 'divider', pt: 2 }}>
              <Typography align="center" variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                O ingresa con:
              </Typography>
              <Button
                fullWidth
                variant="outlined"
                color="primary"
                sx={{ mb: 1, textTransform: 'none' }}
                href={import.meta.env.PROD ? '/accounts/google/login/' : 'http://localhost:8000/accounts/google/login/'}
              >
                <img src="https://authjs.dev/img/providers/google.svg" alt="Google" style={{ width: 20, marginRight: 10 }} />
                Continuar con Google
              </Button>
              <Button
                fullWidth
                variant="outlined"
                color="inherit"
                sx={{ textTransform: 'none' }}
                href={import.meta.env.PROD ? '/accounts/microsoft/login/' : 'http://localhost:8000/accounts/microsoft/login/'}
              >
                <img src="https://authjs.dev/img/providers/microsoft-entra-id.svg" alt="Microsoft" style={{ width: 20, marginRight: 10 }} />
                Continuar con Microsoft
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
