import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, TextField, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, IconButton,
  Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Grid, Alert,
  CircularProgress, FormHelperText, Divider
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, Refresh as RefreshIcon
} from '@mui/icons-material';
import { thirdPartiesService, isDesktop } from '../../services/api';
import { toast } from 'react-toastify';

// Interface matching Django Backend Model
interface ThirdParty {
  id?: number;
  // Identificación
  party_type: 'CLIENTE' | 'PROVEEDOR' | 'EMPLEADO' | 'SOCIO' | 'OTRO';
  person_type: number; // 1: Jurídica, 2: Natural
  identification_type: string;
  identification_number: string;
  check_digit?: string;
  
  // Nombres (Razón Social o Natural)
  business_name?: string;
  trade_name?: string;
  first_name?: string;
  middle_name?: string;
  surname?: string; // Primer Apellido
  second_surname?: string;

  // Ubicación
  country_code: string;
  department_code: string;
  city_code: string;
  postal_code: string;
  address: string;

  // Tributario
  tax_regime: string; // '48', '49', '42'
  fiscal_responsibilities?: string[]; // Requires backend support for JSON
  ciiu_code?: string;

  // Contacto
  email: string;
  phone: string;
  mobile?: string;

  // Banco
  bank_name?: string; 
  bank_account_type?: string; 
  bank_account_number?: string;
  
  is_active?: boolean;
}

interface ThirdPartiesProps {
  partyType?: 'CLIENTE' | 'PROVEEDOR' | 'EMPLEADO' | 'SOCIO' | 'OTRO';
}

const ThirdParties: React.FC<ThirdPartiesProps> = ({ partyType }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [thirdParties, setThirdParties] = useState<ThirdParty[]>([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingThirdParty, setEditingThirdParty] = useState<ThirdParty | null>(null);

  // Initial Form State
  const initialFormState: ThirdParty = {
    party_type: partyType || 'CLIENTE',
    person_type: 1, // Default Jurídica
    identification_type: '31', // Default NIT
    identification_number: '',
    check_digit: '',
    business_name: '',
    trade_name: '',
    first_name: '',
    middle_name: '',
    surname: '',
    second_surname: '',
    country_code: 'CO',
    department_code: '',
    city_code: '',
    postal_code: '',
    address: '',
    tax_regime: '48', // Default Resp. IVA
    fiscal_responsibilities: [],
    ciiu_code: '',
    email: '',
    phone: '',
    mobile: ''
  };

  const [formData, setFormData] = useState<ThirdParty>(initialFormState);

  useEffect(() => {
    loadThirdParties();
  }, [partyType]); // Reload when type changes

  const loadThirdParties = async () => {
    setLoading(true);
    try {
      const filters: any = { search: searchTerm };
      if (partyType) {
        filters.party_type = partyType;
      }
      const data = await thirdPartiesService.getAll(filters);
      setThirdParties(Array.isArray(data) ? data : []);
    } catch (error: any) {
      toast.error('Error al cargar terceros: ' + (error.message || 'Error desconocido'));
      setThirdParties([]);
    } finally {
      setLoading(false);
    }
  };

  const calculateCheckDigit = (nit: string): string => {
    if (!nit) return '';
    const cleanNit = nit.replace(/\D/g, '');
    if (cleanNit.length === 0) return '';
    
    // Pesos para el cálculo de dígito de verificación (de derecha a izquierda)
    // 3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71
    const weights = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71];
    let total = 0;
    
    // Reverse NIT to match weights right-to-left
    const reversedNit = cleanNit.split('').reverse().join('');
    
    for (let i = 0; i < reversedNit.length && i < weights.length; i++) {
      total += parseInt(reversedNit[i]) * weights[i];
    }
    
    const remainder = total % 11;
    if (remainder === 0 || remainder === 1) return remainder.toString();
    return (11 - remainder).toString();
  };

  // Update DV when ID number changes if NIT
  useEffect(() => {
    if (formData.identification_type === '31' && formData.identification_number) {
      const dv = calculateCheckDigit(formData.identification_number);
      setFormData(prev => ({ ...prev, check_digit: dv }));
    }
  }, [formData.identification_number, formData.identification_type]);

  const handleOpenDialog = (thirdParty?: ThirdParty) => {
    if (thirdParty) {
      setEditingThirdParty(thirdParty);
      setFormData(thirdParty);
    } else {
      setEditingThirdParty(null);
      setFormData(initialFormState);
    }
    setOpenDialog(true);
  };

  const handleSubmit = async () => {
    try {
      // Basic Validation
      if (!formData.identification_number) throw new Error("El número de identificación es obligatorio.");
      if (formData.person_type === 1 && !formData.business_name) throw new Error("La Razón Social es obligatoria para Persona Jurídica.");
      if (formData.person_type === 2 && (!formData.first_name || !formData.surname)) throw new Error("Nombre y Apellido son obligatorios para Persona Natural.");

      if (editingThirdParty) {
        await thirdPartiesService.update(editingThirdParty.id!, formData);
        toast.success('Tercero actualizado correctamente');
      } else {
        await thirdPartiesService.create(formData);
        toast.success('Tercero creado correctamente');
      }
      setOpenDialog(false);
      loadThirdParties();
    } catch (error: any) {
      toast.error('Error: ' + (error.message || 'Error desconocido'));
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Está seguro de eliminar este tercero?')) {
      try {
        await thirdPartiesService.delete(id);
        toast.success('Tercero eliminado correctamente');
        loadThirdParties();
      } catch (error: any) {
        toast.error('Error al eliminar: ' + (error.message || 'Error desconocido'));
      }
    }
  };

  const getFullName = (tp: ThirdParty) => {
    if (tp.person_type === 1) return tp.business_name;
    return `${tp.first_name || ''} ${tp.middle_name || ''} ${tp.surname || ''} ${tp.second_surname || ''}`.trim();
  };

  const filteredThirdParties = thirdParties.filter(
    (tp) =>
      tp.identification_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      getFullName(tp)?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          {partyType === 'PROVEEDOR' ? 'Gestión de Proveedores' : 
           partyType === 'CLIENTE' ? 'Gestión de Clientes' : 
           'Gestión de Terceros'}
        </Typography>
        <Box>
          {isDesktop() && (
            <Chip label="Modo Desktop" color="primary" size="small" sx={{ mr: 2 }} />
          )}
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
            Nuevo {partyType === 'PROVEEDOR' ? 'Proveedor' : partyType === 'CLIENTE' ? 'Cliente' : 'Tercero'}
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Box display="flex" gap={2} mb={3}>
          <TextField
            fullWidth
            label="Buscar por NIT, nombre o razón social"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadThirdParties}>
            Actualizar
          </Button>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : thirdParties.length === 0 ? (
          <Alert severity="info">
            No hay terceros registrados. Haz clic en "Nuevo Tercero" para crear uno.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Documento</TableCell>
                  <TableCell>Nombre / Razón Social</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Teléfono</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredThirdParties.map((tp) => (
                  <TableRow key={tp.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="bold">
                        {tp.identification_number}
                        {tp.identification_type === '31' && tp.check_digit ? `-${tp.check_digit}` : ''}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">{tp.identification_type}</Typography>
                    </TableCell>
                    <TableCell>
                      {getFullName(tp)}
                    </TableCell>
                    <TableCell>
                      <Chip label={tp.party_type} size="small" />
                    </TableCell>
                    <TableCell>{tp.phone}</TableCell>
                    <TableCell>{tp.email}</TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => handleOpenDialog(tp)} color="primary">
                        <EditIcon />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDelete(tp.id!)} color="error">
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Dialog Form */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="lg" fullWidth>
        <DialogTitle>
          {editingThirdParty ? 'Editar Tercero' : 'Nuevo Tercero'} - {formData.person_type === 1 ? 'Persona Jurídica' : 'Persona Natural'}
        </DialogTitle>
        <DialogContent dividers>
          <Grid container spacing={2}>
            
            {/* TIPO DE TERCERO Y PERSONA */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="primary" gutterBottom>INFORMACIÓN BÁSICA</Typography>
              <Divider sx={{ mb: 2 }} />
            </Grid>

            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Tercero</InputLabel>
                <Select
                  value={formData.party_type}
                  onChange={(e) => setFormData({ ...formData, party_type: e.target.value as any })}
                  label="Tipo de Tercero"
                >
                  <MenuItem value="CLIENTE">Cliente</MenuItem>
                  <MenuItem value="PROVEEDOR">Proveedor</MenuItem>
                  <MenuItem value="EMPLEADO">Empleado</MenuItem>
                  <MenuItem value="SOCIO">Socio</MenuItem>
                  <MenuItem value="OTRO">Otro</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Tipo de Persona</InputLabel>
                <Select
                  value={formData.person_type}
                  onChange={(e) => setFormData({ ...formData, person_type: Number(e.target.value) })}
                  label="Tipo de Persona"
                >
                  <MenuItem value={1}>Persona Jurídica</MenuItem>
                  <MenuItem value={2}>Persona Natural</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={6}>
               {/* Spacer */}
            </Grid>

            {/* IDENTIFICACIÓN */}
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Tipo Identificación</InputLabel>
                <Select
                  value={formData.identification_type}
                  onChange={(e) => setFormData({ ...formData, identification_type: e.target.value })}
                  label="Tipo Identificación"
                >
                  <MenuItem value="13">Cédula de ciudadanía</MenuItem>
                  <MenuItem value="31">NIT</MenuItem>
                  <MenuItem value="11">Registro civil</MenuItem>
                  <MenuItem value="12">Tarjeta de identidad</MenuItem>
                  <MenuItem value="21">Tarjeta de extranjería</MenuItem>
                  <MenuItem value="22">Cédula de extranjería</MenuItem>
                  <MenuItem value="41">Pasaporte</MenuItem>
                  <MenuItem value="42">Doc. Identificación Extranjero</MenuItem>
                  <MenuItem value="47">PEP</MenuItem>
                  <MenuItem value="50">NIT de otro país</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Número de Identificación"
                value={formData.identification_number}
                onChange={(e) => setFormData({ ...formData, identification_number: e.target.value })}
                required
              />
            </Grid>

            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                label="DV"
                value={formData.check_digit}
                disabled
                helperText="Calculado Automáticamente para NIT"
              />
            </Grid>

            {/* CAMPOS DE NOMBRE - DINÁMICOS */}
            <Grid item xs={12}>
               <Box mt={2} mb={1}>
                 <Typography variant="subtitle2" color="primary">NOMBRES Y RAZÓN SOCIAL</Typography>
                 <Divider />
               </Box>
            </Grid>

            {formData.person_type === 1 ? (
              // Persona Jurídica
              <>
                <Grid item xs={12} sm={8}>
                  <TextField
                    fullWidth
                    label="Razón Social"
                    value={formData.business_name}
                    onChange={(e) => setFormData({ ...formData, business_name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Nombre Comercial"
                    value={formData.trade_name}
                    onChange={(e) => setFormData({ ...formData, trade_name: e.target.value })}
                  />
                </Grid>
              </>
            ) : (
              // Persona Natural
              <>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Primer Nombre"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Segundo Nombre"
                    value={formData.middle_name}
                    onChange={(e) => setFormData({ ...formData, middle_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Primer Apellido"
                    value={formData.surname}
                    onChange={(e) => setFormData({ ...formData, surname: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Segundo Apellido"
                    value={formData.second_surname}
                    onChange={(e) => setFormData({ ...formData, second_surname: e.target.value })}
                  />
                </Grid>
              </>
            )}

            {/* UBICACIÓN */}
            <Grid item xs={12}>
               <Box mt={2} mb={1}>
                 <Typography variant="subtitle2" color="primary">UBICACIÓN Y DATOS DE CONTACTO</Typography>
                 <Divider />
               </Box>
            </Grid>

            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Dirección Completa"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                required
                helperText="Dirección física completa"
              />
            </Grid>
             <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Código Postal"
                value={formData.postal_code}
                onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                required
                helperText="6 dígitos (Ej: 760001)"
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="País (Cód. ISO)"
                value={formData.country_code}
                onChange={(e) => setFormData({ ...formData, country_code: e.target.value })}
                helperText="Ej: CO"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Depto (Cód. DANE)"
                value={formData.department_code}
                onChange={(e) => setFormData({ ...formData, department_code: e.target.value })}
                helperText="Ej: 76 (Valle)"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Ciudad (Cód. DANE)"
                value={formData.city_code}
                onChange={(e) => setFormData({ ...formData, city_code: e.target.value })}
                helperText="Ej: 76001 (Cali)"
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                helperText="Para envío de Factura Electrónica"
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Teléfono"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                required
              />
            </Grid>
             <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Celular"
                value={formData.mobile}
                onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
              />
            </Grid>
            
            {/* TRIBUTARIAS */}
             <Grid item xs={12}>
               <Box mt={2} mb={1}>
                 <Typography variant="subtitle2" color="primary">INFORMACIÓN TRIBUTARIA</Typography>
                 <Divider />
               </Box>
            </Grid>

            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Régimen Tributario</InputLabel>
                <Select
                  value={formData.tax_regime}
                  onChange={(e) => setFormData({ ...formData, tax_regime: e.target.value })}
                  label="Régimen Tributario"
                >
                  <MenuItem value="48">Responsable de IVA (48)</MenuItem>
                  <MenuItem value="49">No Responsable de IVA (49)</MenuItem>
                  <MenuItem value="42">Régimen Simple (42)</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Responsabilidades Fiscales - Multiple Select */}
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Responsabilidades Fiscales</InputLabel>
                <Select
                  multiple
                  value={formData.fiscal_responsibilities || []}
                  onChange={(e) => {
                    const value = e.target.value;
                    setFormData({
                      ...formData,
                      fiscal_responsibilities: typeof value === 'string' ? value.split(',') : value,
                    });
                  }}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value: string) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                  label="Responsabilidades Fiscales"
                >
                  <MenuItem value="O-13">O-13 Gran Contribuyente</MenuItem>
                  <MenuItem value="O-15">O-15 Autorretenedor</MenuItem>
                  <MenuItem value="O-23">O-23 Agente Retención IVA</MenuItem>
                  <MenuItem value="O-47">O-47 Régimen Simple</MenuItem>
                  <MenuItem value="R-99-PN">R-99-PN No aplica</MenuItem>
                </Select>
              </FormControl>
            </Grid>

             <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="CIIU (Actividad Económica)"
                value={formData.ciiu_code}
                onChange={(e) => setFormData({ ...formData, ciiu_code: e.target.value })}
                helperText="Código para tarifa ICA"
                required
              />
            </Grid>

          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            {editingThirdParty ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ThirdParties;
