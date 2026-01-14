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
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  IconButton
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { accountsService } from '../../services/api';
import { toast } from 'react-toastify';

interface Account {
  id?: number;
  code: string;
  name: string;
  level: number;
  nature: 'DEBITO' | 'CREDITO';
  account_type: string;
  is_active: boolean;
}

const ChartOfAccounts: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [filteredAccounts, setFilteredAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Dialog State
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState<Partial<Account>>({
    code: '',
    name: '',
    nature: 'DEBITO',
    account_type: 'GASTO',
    level: 4,
    is_active: true
  });

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    filterAccounts();
  }, [searchTerm, accounts]);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const data = await accountsService.getAll();
      setAccounts(data);
    } catch (error) {
      console.error(error);
      toast.error('Error al cargar cuentas contables');
    } finally {
      setLoading(false);
    }
  };

  const filterAccounts = () => {
    if (!searchTerm) {
      setFilteredAccounts(accounts);
      return;
    }
    const lowerTerm = searchTerm.toLowerCase();
    const filtered = accounts.filter(acc => 
      acc.code.toLowerCase().includes(lowerTerm) || 
      acc.name.toLowerCase().includes(lowerTerm)
    );
    setFilteredAccounts(filtered);
  };

  const handleCreate = async () => {
    try {
      if (!formData.code || !formData.name) {
        toast.warning('Código y Nombre son obligatorios');
        return;
      }
      await accountsService.create(formData);
      toast.success('Cuenta creada exitosamente');
      setOpenDialog(false);
      loadAccounts();
    } catch (error) {
      console.error(error);
      toast.error('Error al crear cuenta');
    }
  };

  const getNatureColor = (nature: string) => {
    return nature === 'DEBITO' ? 'primary' : 'warning';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Plan Único de Cuentas (PUC)
        </Typography>
        <Box>
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={loadAccounts}
            sx={{ mr: 1 }}
          >
            Refrescar
          </Button>
          <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={() => setOpenDialog(true)}
          >
            Nueva Cuenta
          </Button>
        </Box>
      </Box>

      <Paper sx={{ mb: 2, p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-end' }}>
          <SearchIcon sx={{ color: 'action.active', mr: 1, my: 0.5 }} />
          <TextField 
            fullWidth
            label="Buscar por Código o Nombre" 
            variant="standard"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell><strong>Código</strong></TableCell>
              <TableCell><strong>Nombre</strong></TableCell>
              <TableCell><strong>Tipo</strong></TableCell>
              <TableCell><strong>Naturaleza</strong></TableCell>
              <TableCell><strong>Nivel</strong></TableCell>
              <TableCell><strong>Estado</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <CircularProgress size={24} /> Cargando PUC...
                </TableCell>
              </TableRow>
            ) : filteredAccounts.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No se encontraron cuentas.
                </TableCell>
              </TableRow>
            ) : (
              filteredAccounts.map((account) => (
                <TableRow key={account.id} hover>
                  <TableCell>{account.code}</TableCell>
                  <TableCell>{account.name}</TableCell>
                  <TableCell>
                    <Chip label={account.account_type} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={account.nature} 
                      color={getNatureColor(account.nature)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{account.level}</TableCell>
                  <TableCell>
                    {account.is_active ? 
                      <Chip label="Activa" color="success" size="small" variant="outlined" /> : 
                      <Chip label="Inactiva" color="default" size="small" variant="outlined" />
                    }
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Modal Creación */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>Nueva Cuenta Contable</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Código"
              fullWidth
              value={formData.code}
              onChange={(e) => setFormData({...formData, code: e.target.value})}
            />
            <TextField
              label="Nombre"
              fullWidth
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
            <FormControl fullWidth>
              <InputLabel>Naturaleza</InputLabel>
              <Select
                value={formData.nature}
                label="Naturaleza"
                onChange={(e) => setFormData({...formData, nature: e.target.value as any})}
              >
                <MenuItem value="DEBITO">Débito</MenuItem>
                <MenuItem value="CREDITO">Crédito</MenuItem>
              </Select>
            </FormControl>
             <FormControl fullWidth>
              <InputLabel>Tipo</InputLabel>
              <Select
                value={formData.account_type}
                label="Tipo"
                onChange={(e) => setFormData({...formData, account_type: e.target.value as any})}
              >
                <MenuItem value="ACTIVO">Activo</MenuItem>
                <MenuItem value="PASIVO">Pasivo</MenuItem>
                <MenuItem value="PATRIMONIO">Patrimonio</MenuItem>
                <MenuItem value="INGRESO">Ingreso</MenuItem>
                <MenuItem value="GASTO">Gasto</MenuItem>
                <MenuItem value="COSTO">Costo</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleCreate}>Guardar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ChartOfAccounts;
