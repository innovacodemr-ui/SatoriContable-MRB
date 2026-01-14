import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  TextField,
  Grid,
  Step,
  StepLabel,
  Stepper
} from '@mui/material';
import {
  CloudDownload as LoadIcon,
  CheckCircle as SuccessIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { isDesktop, tenantService } from '../services/api';
import { toast } from 'react-toastify';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const InitialSetup: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const { clientId, login } = useAuth(); // We need login to update clientId in context
  const navigate = useNavigate();

  // Company Form State
  const [companyData, setCompanyData] = useState({
    name: '',
    legal_name: '',
    nit: '',
    email: '',
    phone: ''
  });

  // Desktop Setup State
  const [desktopStep, setDesktopStep] = useState<'idle' | 'puc' | 'data' | 'complete'>('idle');

  useEffect(() => {
    // Determine initial step based on clientId presence
    if (clientId) {
      if (isDesktop()) {
        setActiveStep(1); // Skip to Demo Data if company exists and is desktop
      } else {
        // If web and company exists, maybe we are done?
        // But if user accessed /setup manually, we show status.
        setActiveStep(2);
      }
    }
  }, [clientId]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCompanyData({ ...companyData, [e.target.name]: e.target.value });
  };

  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData();
      Object.keys(companyData).forEach(key => {
        formData.append(key, (companyData as any)[key]);
      });

      const newCompany = await tenantService.createCompany(formData);

      toast.success('¡Empresa creada exitosamente!');

      // Update Auth Context with new Client ID
      // We re-login with same tokens but new client ID to refresh context
      const access = localStorage.getItem('access_token');
      const refresh = localStorage.getItem('refresh_token');
      if (access && refresh) {
        await login(access, refresh, newCompany.id.toString());
      }

      if (isDesktop()) {
        setActiveStep(1);
      } else {
        setActiveStep(1); // Finish for Web (Index 1)
      }

    } catch (error: any) {
      console.error(error);
      toast.error('Error creando empresa: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleDesktopSetup = async () => {
    if (!window.confirm('¿Desea cargar los datos de prueba? (PUC, Terceros, Facturas)')) {
      return;
    }

    setLoading(true);
    setDesktopStep('puc');

    try {
      // Paso 1: Cargar PUC
      // console.log('Cargando PUC...');
      const pucResult = await window.electronAPI!.loadPUC();

      if (!pucResult.success) {
        throw new Error('Error al cargar PUC: ' + pucResult.error);
      }

      toast.success(`✅ PUC cargado: ${pucResult.inserted} cuentas insertadas`);

      await new Promise(resolve => setTimeout(resolve, 500));

      // Paso 2: Cargar datos de prueba
      setDesktopStep('data');
      const dataResult = await window.electronAPI!.loadTestData();

      if (!dataResult.success) {
        throw new Error('Error al cargar datos: ' + dataResult.error);
      }

      toast.success(`✅ Datos cargados: ${dataResult.thirdParties} terceros, ${dataResult.journalEntries} comprobantes`);

      setDesktopStep('complete');
      setTimeout(() => {
        setActiveStep(2);
      }, 1000);

    } catch (error: any) {
      toast.error('Error: ' + error.message);
      setDesktopStep('idle');
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    'Crear Empresa',
    ...(isDesktop() ? ['Cargar Datos Demo'] : []),
    'Finalizar'
  ];

  const completionStepIndex = steps.length - 1;

  const renderCompanyForm = () => (
    <Box component="form" onSubmit={handleCreateCompany} sx={{ mt: 2 }}>
      <Typography variant="body1" gutterBottom sx={{ mb: 3 }}>
        Para comenzar, necesitamos registrar los datos básicos de tu primera empresa o cliente.
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12}>
          <TextField
            fullWidth label="Razón Social (Legal)" name="legal_name"
            value={companyData.legal_name} onChange={handleInputChange} required
            placeholder="Ej: Inversiones Satori S.A.S"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth label="Nombre Comercial" name="name"
            value={companyData.name} onChange={handleInputChange} required
            placeholder="Ej: Satori Contable"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth label="NIT" name="nit"
            value={companyData.nit} onChange={handleInputChange} required
            placeholder="Ej: 900123456"
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth label="Email Corporativo" name="email" type="email"
            value={companyData.email} onChange={handleInputChange}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            fullWidth label="Teléfono" name="phone"
            value={companyData.phone} onChange={handleInputChange}
          />
        </Grid>
        <Grid item xs={12}>
          <Button
            type="submit" variant="contained" fullWidth size="large"
            disabled={loading} sx={{ mt: 2 }}
          >
            {loading ? <CircularProgress size={24} color="inherit" /> : 'Crear Empresa y Continuar'}
          </Button>
        </Grid>
      </Grid>
    </Box>
  );

  const renderDesktopSetup = () => (
    <Box sx={{ mt: 2, textAlign: 'center' }}>
      <Typography variant="body1" gutterBottom>
        Como estás en la versión de Escritorio, podemos cargar datos de ejemplo para que pruebes el sistema.
      </Typography>

      <Button
        variant="outlined"
        size="large"
        startIcon={loading ? <CircularProgress size={20} /> : <LoadIcon />}
        onClick={handleDesktopSetup}
        disabled={loading || desktopStep === 'complete'}
        sx={{ my: 3 }}
      >
        {loading ? 'Procesando...' : desktopStep === 'complete' ? 'Carga Completa' : 'Cargar Datos de Prueba'}
      </Button>

      {desktopStep !== 'idle' && (
        <List dense sx={{ maxWidth: 300, mx: 'auto' }}>
          <ListItem>
            <SuccessIcon color={(desktopStep as any) !== 'idle' ? 'success' : 'disabled'} sx={{ mr: 1 }} />
            <ListItemText primary="Plan de Cuentas (PUC)" />
          </ListItem>
          <ListItem>
            <SuccessIcon color={desktopStep === 'data' || desktopStep === 'complete' ? 'success' : 'disabled'} sx={{ mr: 1 }} />
            <ListItemText primary="Terceros y Facturas" />
          </ListItem>
        </List>
      )}

      <Box sx={{ mt: 2 }}>
        <Button onClick={() => setActiveStep(completionStepIndex)} color="inherit">
          Saltar este paso
        </Button>
      </Box>
    </Box>
  );

  const renderCompletion = () => (
    <Box sx={{ textAlign: 'center', mt: 4 }}>
      <SuccessIcon color="success" sx={{ fontSize: 60, mb: 2 }} />
      <Typography variant="h5" gutterBottom>
        ¡Todo Listo!
      </Typography>
      <Typography color="textSecondary" paragraph>
        Tu empresa ha sido configurada correctamente. Ya puedes empezar a gestionar tu contabilidad.
      </Typography>
      <Button
        variant="contained"
        size="large"
        onClick={() => navigate('/')}
        sx={{ mt: 2 }}
      >
        Ir al Dashboard
      </Button>
    </Box>
  );

  return (
    <Box sx={{ p: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 700 }}>
        <Typography variant="h4" fontWeight="bold" textAlign="center" gutterBottom>
          Bienvenido a Satori
        </Typography>

        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {activeStep === 0 && !clientId && renderCompanyForm()}
        {activeStep === 0 && clientId && (
          <Alert severity="info">
            Ya tienes una empresa asociada. <Button onClick={() => setActiveStep(isDesktop() ? 1 : completionStepIndex)}>Continuar</Button>
          </Alert>
        )}

        {activeStep === 1 && isDesktop() && renderDesktopSetup()}

        {activeStep === completionStepIndex && renderCompletion()}

      </Paper>
    </Box>
  );
};

export default InitialSetup;
