import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Grid,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { accountsService, dianService, isDesktop } from '../../services/api';
import { toast } from 'react-toastify';

interface Account {
  id?: number;
  code: string;
  name: string;
  level: number;
  nature: 'DEBITO' | 'CREDITO';
  account_type: 'ACTIVO' | 'PASIVO' | 'PATRIMONIO' | 'INGRESO' | 'GASTO' | 'COSTO';
  allows_movement: boolean;
  requires_third_party: boolean;
  requires_cost_center: boolean;
  is_tax_account: boolean;
  tax_type?: string;
  // Exógena (Multiple configurations)
  dian_configurations?: { id?: number; dian_format: number; dian_concept: number; format_code?: string; concept_code?: string }[];
}

const Accounts: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [dianFormats, setDianFormats] = useState<any[]>([]);
  const [dianConcepts, setDianConcepts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [formData, setFormData] = useState<Partial<Account>>({
    code: '',
    name: '',
    level: 6,
    nature: 'DEBITO',
    account_type: 'ACTIVO',
    allows_movement: true,
    requires_third_party: false,
    requires_cost_center: false,
    is_tax_account: false,
    tax_type: '',
    dian_configurations: []
  });

  // Cargar cuentas
  useEffect(() => {
    loadAccounts();
    loadDianData();
  }, []);

  const loadDianData = async () => {
    try {
      const formats = await dianService.getFormats();
      setDianFormats(Array.isArray(formats) ? formats : []);
      
      const concepts = await dianService.getConcepts();
      setDianConcepts(Array.isArray(concepts) ? concepts : []);
    } catch (e) {
      console.error('Error loading DIAN data', e);
    }
  };

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const data = await accountsService.getAll({ search: searchTerm });
      setAccounts(Array.isArray(data) ? data : []);
    } catch (error: any) {
      toast.error('Error al cargar cuentas: ' + (error.message || 'Error desconocido'));
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (account?: Account) => {
    // Recargar datos DIAN por si hubo cambios recientes
    loadDianData();
    
    if (account) {
      setEditingAccount(account);
      setFormData(account);
    } else {
      setEditingAccount(null);
      setFormData({
        code: '',
        name: '',
        level: 6,
        nature: 'DEBITO',
        account_type: 'ACTIVO',
        allows_movement: true,
        requires_third_party: false,
        requires_cost_center: false,
        is_tax_account: false,
        tax_type: '',
        dian_configurations: []
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingAccount(null);
  };

  const handleSubmit = async () => {
    try {
      if (editingAccount) {
        await accountsService.update(editingAccount.id!, formData as Account);
        toast.success('Cuenta actualizada correctamente');
      } else {
        await accountsService.create(formData as Account);
        toast.success('Cuenta creada correctamente');
      }
      handleCloseDialog();
      loadAccounts();
    } catch (error: any) {
      toast.error('Error: ' + (error.message || 'Error desconocido'));
    }
  };

  const handleLoadPUC = async () => {
    if (!isDesktop()) {
      toast.error('Esta función solo está disponible en Desktop');
      return;
    }

    if (!window.confirm('¿Desea cargar el PUC completo? Esto agregará cientos de cuentas a la base de datos.')) {
      return;
    }

    setLoading(true);
    try {
      const result = await window.electronAPI!.loadPUC();
      if (result.success) {
        toast.success(
          `PUC cargado correctamente:\n✓ ${result.inserted} cuentas insertadas\n⊘ ${result.skipped} omitidas (duplicadas)\n✗ ${result.errors} errores\n📊 Total: ${result.total} cuentas`
        );
        loadAccounts();
      } else {
        toast.error('Error al cargar PUC: ' + result.error);
      }
    } catch (error: any) {
      toast.error('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Está seguro de eliminar esta cuenta?')) {
      try {
        await accountsService.delete(id);
        toast.success('Cuenta eliminada correctamente');
        loadAccounts();
      } catch (error: any) {
        toast.error('Error al eliminar: ' + (error.message || 'Error desconocido'));
      }
    }
  };

  const filteredAccounts = accounts.filter(
    (account) =>
      account.code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      account.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Plan Único de Cuentas (PUC)
        </Typography>
        <Box>
          {isDesktop() && (
            <>
              <Chip
                label="Modo Desktop"
                color="primary"
                size="small"
                sx={{ mr: 2 }}
              />
              <Button
                variant="outlined"
                color="secondary"
                size="small"
                sx={{ mr: 2 }}
                onClick={handleLoadPUC}
                disabled={loading}
              >
                Cargar PUC Completo
              </Button>
            </>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Nueva Cuenta
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Box display="flex" gap={2} mb={3}>
          <TextField
            fullWidth
            label="Buscar por código o nombre"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Ej: 1105 o Caja"
          />
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAccounts}
          >
            Actualizar
          </Button>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : accounts.length === 0 ? (
          <Alert severity="info">
            No hay cuentas registradas. Haz clic en "Nueva Cuenta" para crear una.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Código</TableCell>
                  <TableCell>Nombre</TableCell>
                  <TableCell>Nivel</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Naturaleza</TableCell>
                  <TableCell>Permite Movimiento</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredAccounts.map((account) => (
                  <TableRow key={account.id} hover>
                    <TableCell>
                      <Typography fontFamily="monospace" fontWeight="bold">
                        {account.code}
                      </Typography>
                    </TableCell>
                    <TableCell>{account.name}</TableCell>
                    <TableCell>{account.level}</TableCell>
                    <TableCell>
                      <Chip
                        label={account.account_type}
                        size="small"
                        color={
                          account.account_type === 'ACTIVO'
                            ? 'success'
                            : account.account_type === 'PASIVO'
                            ? 'error'
                            : account.account_type === 'PATRIMONIO'
                            ? 'warning'
                            : 'info'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={account.nature}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {account.allows_movement ? '✓' : '✗'}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(account)}
                        color="primary"
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(account.id!)}
                        color="error"
                      >
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

      {/* Dialog de Crear/Editar */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingAccount ? 'Editar Cuenta' : 'Nueva Cuenta'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Código"
                value={formData.code}
                onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                placeholder="110505"
                required
              />
            </Grid>
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Nombre"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Nivel</InputLabel>
                <Select
                  value={formData.level}
                  onChange={(e) => setFormData({ ...formData, level: Number(e.target.value) })}
                  label="Nivel"
                >
                  <MenuItem value={1}>1 - Clase</MenuItem>
                  <MenuItem value={2}>2 - Grupo</MenuItem>
                  <MenuItem value={3}>3 - Cuenta</MenuItem>
                  <MenuItem value={4}>4 - Subcuenta</MenuItem>
                  <MenuItem value={5}>5 - Auxiliar 1</MenuItem>
                  <MenuItem value={6}>6 - Auxiliar 2</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={formData.account_type}
                  onChange={(e) => setFormData({ ...formData, account_type: e.target.value as any })}
                  label="Tipo"
                >
                  <MenuItem value="ACTIVO">Activo</MenuItem>
                  <MenuItem value="PASIVO">Pasivo</MenuItem>
                  <MenuItem value="PATRIMONIO">Patrimonio</MenuItem>
                  <MenuItem value="INGRESO">Ingreso</MenuItem>
                  <MenuItem value="GASTO">Gasto</MenuItem>
                  <MenuItem value="COSTO">Costo</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Naturaleza</InputLabel>
                <Select
                  value={formData.nature}
                  onChange={(e) => setFormData({ ...formData, nature: e.target.value as any })}
                  label="Naturaleza"
                >
                  <MenuItem value="DEBITO">Débito</MenuItem>
                  <MenuItem value="CREDITO">Crédito</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.allows_movement}
                    onChange={(e) => setFormData({ ...formData, allows_movement: e.target.checked })}
                  />
                }
                label="Permite movimiento"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.requires_third_party}
                    onChange={(e) => setFormData({ ...formData, requires_third_party: e.target.checked })}
                  />
                }
                label="Requiere tercero"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.requires_cost_center}
                    onChange={(e) => setFormData({ ...formData, requires_cost_center: e.target.checked })}
                  />
                }
                label="Requiere centro de costo"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_tax_account}
                    onChange={(e) => setFormData({ ...formData, is_tax_account: e.target.checked })}
                  />
                }
                label="Cuenta de impuestos"
              />
            </Grid>
            {formData.is_tax_account && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Tipo de impuesto"
                  value={formData.tax_type}
                  onChange={(e) => setFormData({ ...formData, tax_type: e.target.value })}
                  placeholder="IVA, RETEFUENTE, etc."
                />
              </Grid>
            )}

            {/* Medios Magnéticos */}
             <Grid item xs={12}>
               <Box mt={2} mb={1}>
                 <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Typography variant="subtitle2" color="primary">MEDIOS MAGNÉTICOS (EXÓGENA DIAN)</Typography>
                    <Button 
                      size="small" 
                      startIcon={<AddIcon />} 
                      onClick={() => {
                         const current = formData.dian_configurations || [];
                         if (current.length < 5) {
                            setFormData({ ...formData, dian_configurations: [...current, { dian_format: 0, dian_concept: 0 }] });
                         }
                      }}
                      disabled={(formData.dian_configurations?.length || 0) >= 5}
                    >
                      Agregar ({formData.dian_configurations?.length || 0}/5)
                    </Button>
                 </Box>
                 <Divider sx={{ mb: 2 }} />
                 
                 {(formData.dian_configurations || []).map((config, index) => (
                    <Grid container spacing={2} key={index} sx={{ mb: 1 }} alignItems="center">
                        <Grid item xs={5}>
                           <FormControl fullWidth size="small">
                              <InputLabel>Formato</InputLabel>
                              <Select
                                value={config.dian_format || ''}
                                label="Formato"
                                onChange={(e) => {
                                   const newConfigs = [...(formData.dian_configurations || [])];
                                   newConfigs[index].dian_format = Number(e.target.value);
                                   newConfigs[index].dian_concept = 0; // Reset concept
                                   setFormData({ ...formData, dian_configurations: newConfigs });
                                }}
                              >
                                 <MenuItem value={0}><em>Seleccionar</em></MenuItem>
                                 {dianFormats.map(fmt => (
                                   <MenuItem key={fmt.id} value={fmt.id}>
                                      {fmt.code} - {fmt.name}
                                   </MenuItem>
                                 ))}
                              </Select>
                           </FormControl>
                        </Grid>
                        <Grid item xs={5}>
                           <FormControl fullWidth size="small">
                              <InputLabel>Concepto</InputLabel>
                              <Select
                                value={config.dian_concept || ''}
                                label="Concepto"
                                disabled={!config.dian_format}
                                onChange={(e) => {
                                   const newConfigs = [...(formData.dian_configurations || [])];
                                   newConfigs[index].dian_concept = Number(e.target.value);
                                   setFormData({ ...formData, dian_configurations: newConfigs });
                                }}
                              >
                                 <MenuItem value={0}><em>Seleccionar</em></MenuItem>
                                 {dianConcepts
                                    .filter(c => c.format === config.dian_format)
                                    .map(concept => (
                                       <MenuItem key={concept.id} value={concept.id}>
                                          {concept.code} - {concept.name}
                                       </MenuItem>
                                    ))}
                              </Select>
                           </FormControl>
                        </Grid>
                        <Grid item xs={2}>
                             <IconButton 
                               size="small" 
                               color="error" 
                               onClick={() => {
                                  const newConfigs = (formData.dian_configurations || []).filter((_, i) => i !== index);
                                  setFormData({ ...formData, dian_configurations: newConfigs });
                               }}
                             >
                                <DeleteIcon />
                             </IconButton>
                        </Grid>
                    </Grid>
                 ))}
                 {(formData.dian_configurations?.length === 0) && (
                     <Typography variant="body2" color="textSecondary" align="center">
                        No hay formatos asignados.
                     </Typography>
                 )}
               </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            {editingAccount ? 'Actualizar' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Accounts;
