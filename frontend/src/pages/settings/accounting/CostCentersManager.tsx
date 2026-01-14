import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  IconButton,
  Autocomplete,
  Chip
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, AccountTree as TreeIcon } from '@mui/icons-material';
import accountingService, { CostCenter } from '../../../services/accountingService';
import { toast } from 'react-toastify';

const CostCentersManager: React.FC = () => {
  const [costCenters, setCostCenters] = useState<CostCenter[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  const [currentCostCenter, setCurrentCostCenter] = useState<Partial<CostCenter>>({
    code: '',
    name: '',
    description: '',
    parent: null,
    is_active: true
  });

  useEffect(() => {
    loadCostCenters();
  }, []);

  const loadCostCenters = async () => {
    try {
      setLoading(true);
      const data = await accountingService.getCostCenters();
      // If paginated
      let centers: CostCenter[] = Array.isArray(data) ? data : data.results;
      // Sort by code to show hierarchy somewhat
      centers.sort((a, b) => a.code.localeCompare(b.code));
      setCostCenters(centers);
    } catch (error) {
      console.error(error);
      toast.error('Error cargando centros de costo');
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = (center?: CostCenter) => {
    if (center) {
      setCurrentCostCenter(center);
      setIsEditing(true);
    } else {
      setCurrentCostCenter({
        code: '',
        name: '',
        description: '',
        parent: null,
        is_active: true
      });
      setIsEditing(false);
    }
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  const handleSave = async () => {
    try {
      if (!currentCostCenter.code || !currentCostCenter.name) {
        toast.warning('Código y Nombre son obligatorios');
        return;
      }

      if (isEditing && currentCostCenter.id) {
        await accountingService.updateCostCenter(currentCostCenter.id, currentCostCenter as CostCenter);
        toast.success('Centro de Costo actualizado');
      } else {
        await accountingService.createCostCenter(currentCostCenter as CostCenter);
        toast.success('Centro de Costo creado');
      }
      handleClose();
      loadCostCenters();
    } catch (error) {
      console.error(error);
      toast.error('Error guardando centro de costo');
    }
  };

  // Find parent object for checking display or logic
  const getParentName = (parentId?: number | null) => {
    if (!parentId) return '-';
    const parent = costCenters.find(c => c.id === parentId);
    return parent ? `${parent.code} - ${parent.name}` : 'Desconocido';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TreeIcon /> Centros de Costo
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()}>
          Nuevo Centro
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Código</TableCell>
              <TableCell>Nombre</TableCell>
              <TableCell>Padre</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {costCenters.map((center) => (
              <TableRow key={center.id} hover>
                <TableCell sx={{ fontWeight: 'bold' }}>{center.code}</TableCell>
                <TableCell>{center.name}</TableCell>
                <TableCell>{getParentName(center.parent)}</TableCell>
                <TableCell>
                    <Chip 
                        label={center.is_active ? 'Activo' : 'Inactivo'} 
                        color={center.is_active ? 'success' : 'default'}
                        size="small" 
                    />
                </TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => handleOpen(center)} size="small"><EditIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {costCenters.length === 0 && !loading && (
                <TableRow>
                    <TableCell colSpan={5} align="center">No hay centros de costo definidos.</TableCell>
                </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? 'Editar Centro de Costo' : 'Nuevo Centro de Costo'}</DialogTitle>
        <DialogContent dividers>
          <Box display="flex" flexDirection="column" gap={3}>
            
            <Autocomplete
                options={costCenters.filter(c => c.id !== currentCostCenter.id)} // Prevent self-parenting
                getOptionLabel={(option) => `${option.code} - ${option.name}`}
                value={costCenters.find(c => c.id === currentCostCenter.parent) || null}
                onChange={(_, newValue) => {
                    setCurrentCostCenter({ ...currentCostCenter, parent: newValue ? newValue.id : null });
                }}
                renderInput={(params) => <TextField {...params} label="Centro Padre (Opcional)" helperText="Selecciona si es un sub-centro" />}
            />

            <Box display="flex" gap={2}>
              <TextField
                label="Código"
                value={currentCostCenter.code}
                onChange={(e) => setCurrentCostCenter({ ...currentCostCenter, code: e.target.value })}
                required
                fullWidth
                helperText="Ej: 01, 10-05"
              />
            </Box>

            <TextField
              label="Nombre"
              value={currentCostCenter.name}
              onChange={(e) => setCurrentCostCenter({ ...currentCostCenter, name: e.target.value })}
              required
              fullWidth
            />
            
            <TextField
              label="Descripción"
              value={currentCostCenter.description}
              onChange={(e) => setCurrentCostCenter({ ...currentCostCenter, description: e.target.value })}
              multiline
              rows={2}
              fullWidth
            />

          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancelar</Button>
          <Button variant="contained" onClick={handleSave}>Guardar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CostCentersManager;
