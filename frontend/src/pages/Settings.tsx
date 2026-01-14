import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Grid,
  TextField,
  Button,
  Avatar,
  Divider,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  CardHeader,
  Chip
} from '@mui/material';
import { tenantService } from '../services/api';
import { useAuth } from '../context/AuthContext';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import SecurityIcon from '@mui/icons-material/Security';
import BusinessIcon from '@mui/icons-material/Business';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [hasCertificate, setHasCertificate] = useState(false);
  
  // Form State
  const [formData, setFormData] = useState({
    name: '',
    nit: '',
    legal_name: '',
    email: '',
    phone: '',
    address: '',
    dian_test_set_id: '',
    dian_software_id: '',
    certificate_password: ''
  });

  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [certFile, setCertFile] = useState<File | null>(null);

  const { updateClientName } = useAuth();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const data = await tenantService.getCompanySettings();
      setCompanyId(data.id);
      setHasCertificate(data.has_certificate);
      setFormData({
        name: data.name || '',
        nit: data.nit || '',
        legal_name: data.legal_name || '',
        email: data.email || '',
        phone: data.phone || '',
        address: data.address || '',
        dian_test_set_id: data.dian_test_set_id || '',
        dian_software_id: data.dian_software_id || '',
        certificate_password: '' // Never populated from backend for security
      });
      if (data.logo) {
         setLogoPreview(data.logo);
      }
    } catch (err: any) {
      console.error(err);
      // Si es un error 404/400 de que no existe empresa, no mostramos error, dejamos que cree una
      if (err.response && (err.response.status === 404 || err.response.status === 400)) {
          console.log("No existe empresa configurada, permitiendo creación.");
          // No seteamos message error, dejamos formulario limpio
      } else {
          setMessage({ type: 'error', text: 'Error cargando configuración.' });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setLogoFile(file);
      setLogoPreview(URL.createObjectURL(file));
    }
  };

  const handleCertChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setCertFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setSaving(true);
    setMessage(null);

    try {
      const data = new FormData();
      // Append text fields
      Object.keys(formData).forEach(key => {
        // Only append password if user typed something
        if (key === 'certificate_password') {
            if (formData[key]) data.append(key, formData[key]);
        } else {
            data.append(key, (formData as any)[key]);
        }
      });
      
      // Append files
      if (logoFile) {
        data.append('logo', logoFile);
      }
      if (certFile) {
        data.append('dian_certificate', certFile);
      }

      if (companyId) {
          // Actualizar existente
          await tenantService.updateCompanySettings(companyId, data);
          setMessage({ type: 'success', text: 'Configuración actualizada exitosamente.' });
      } else {
          // Crear nueva empresa
          const newCompany = await tenantService.createCompany(data);
          setMessage({ type: 'success', text: 'Empresa creada exitosamente.' });
          
          if (newCompany && newCompany.id) {
              setCompanyId(newCompany.id);
              // IMPORTANTE: Guardar en localStorage para futuras peticiones (X-Client-Id)
              localStorage.setItem('client_id', newCompany.id.toString());
          }
      }
      
      // Clear sensitive fields
      setFormData(prev => ({ ...prev, certificate_password: '' }));
      setCertFile(null);
      
      // Reload settings to get updated logo URL etc
      loadSettings();
      // Update global context with new name
      await updateClientName();

    } catch (err) {
      console.error(err);
      setMessage({ type: 'error', text: 'Error guardando configuración.' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}><CircularProgress /></Box>;

  return (
    <Box sx={{ p: 4, maxWidth: 1200, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 'bold' }}>
        Configuración de Empresa
      </Typography>
      
      {message && (
        <Alert severity={message.type} sx={{ mb: 3 }}>
          {message.text}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          
          {/* Tarjeta Identidad Corporativa */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardHeader 
                avatar={<Avatar sx={{ bgcolor: 'secondary.main' }}><BusinessIcon /></Avatar>}
                title="Identidad Corporativa"
                subheader="Datos legales y visuales"
              />
              <Divider />
              <CardContent>
                <Grid container spacing={2}>
                    <Grid item xs={12} sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
                        <Avatar 
                            src={logoPreview || undefined} 
                            sx={{ width: 100, height: 100, mb: 2, border: '1px solid #eee' }}
                            variant="rounded"
                        >
                            LOGO
                        </Avatar>
                        <Button
                            variant="outlined"
                            component="label"
                            size="small"
                            startIcon={<CloudUploadIcon />}
                        >
                            Subir Logo
                            <input type="file" hidden accept="image/*" onChange={handleLogoChange} />
                        </Button>
                    </Grid>
                    
                    <Grid item xs={12}>
                        <TextField fullWidth label="Razón Social" name="legal_name" value={formData.legal_name} onChange={handleInputChange} required />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField fullWidth label="Nombre Comercial" name="name" value={formData.name} onChange={handleInputChange} required />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField fullWidth label="NIT" name="nit" value={formData.nit} onChange={handleInputChange} required />
                    </Grid>
                    <Grid item xs={12}>
                        <TextField fullWidth label="Dirección" name="address" value={formData.address} onChange={handleInputChange} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField fullWidth label="Email" name="email" value={formData.email} onChange={handleInputChange} />
                    </Grid>
                    <Grid item xs={12} md={6}>
                        <TextField fullWidth label="Teléfono" name="phone" value={formData.phone} onChange={handleInputChange} />
                    </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Tarjeta Nómina Electrónica (Zona Segura) */}
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ height: '100%', borderColor: 'primary.light' }}>
               <CardHeader 
                avatar={<Avatar sx={{ bgcolor: 'primary.main' }}><SecurityIcon /></Avatar>}
                title="Habilitación DIAN"
                subheader="Certificados y Credenciales"
              />
              <Divider />
              <CardContent>
                <Alert severity="info" sx={{ mb: 3 }}>
                    Esta información se usa para firmar digitalmente los XML enviados a la DIAN.
                </Alert>
                
                <Grid container spacing={3}>
                    <Grid item xs={12}>
                        <Box sx={{ border: '2px dashed #ccc', p: 3, textAlign: 'center', borderRadius: 2 }}>
                            <Box sx={{ mb: 2 }}>
                                {hasCertificate ? (
                                    <Chip 
                                        icon={<CheckCircleIcon />} 
                                        label="Certificado Activo y Configurado" 
                                        color="success" 
                                        variant="outlined"
                                    />
                                ) : (
                                    <Chip 
                                        icon={<ErrorOutlineIcon />} 
                                        label="Certificado No Configurado" 
                                        color="error" 
                                        variant="outlined"
                                    />
                                )}
                            </Box>
                            
                            <Typography gutterBottom>Actualizar Certificado Digital (.p12)</Typography>
                            <Button
                                variant="contained"
                                component="label"
                                startIcon={<CloudUploadIcon />}
                                color="success"
                            >
                                Seleccionar Archivo
                                <input type="file" hidden accept=".p12,.pfx" onChange={handleCertChange} />
                            </Button>
                            {certFile && (
                                <Typography variant="caption" display="block" sx={{ mt: 1, color: 'success.main', fontWeight: 'bold' }}>
                                    Archivo seleccionado: {certFile.name}
                                </Typography>
                            )}
                        </Box>
                    </Grid>

                    <Grid item xs={12}>
                        <TextField 
                            fullWidth 
                            label="Contraseña del Certificado" 
                            name="certificate_password" 
                            type="password"
                            value={formData.certificate_password} 
                            onChange={handleInputChange}
                            helperText="Ingrese solo si desea actualizar la contraseña"
                        />
                    </Grid>
                    
                    <Grid item xs={12}>
                        <Divider sx={{ my: 2 }}>
                            <Typography variant="caption" color="text.secondary">SOFTWARE DIAN</Typography>
                        </Divider>
                    </Grid>

                    <Grid item xs={12}>
                         <TextField fullWidth label="ID Software" name="dian_software_id" value={formData.dian_software_id} onChange={handleInputChange} />
                    </Grid>
                    <Grid item xs={12}>
                         <TextField fullWidth label="Test Set ID" name="dian_test_set_id" value={formData.dian_test_set_id} onChange={handleInputChange} />
                    </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sx={{ mb: 4, display: 'flex', justifyContent: 'flex-end' }}>
             <Button 
                type="submit" 
                variant="contained" 
                size="large" 
                disabled={saving}
                sx={{ px: 5, py: 1.5 }}
             >
                 {saving ? <CircularProgress size={24} color="inherit" /> : 'GUARDAR CONFIGURACIÓN'}
             </Button>
          </Grid>

        </Grid>
      </form>
    </Box>
  );
};

export default Settings;
