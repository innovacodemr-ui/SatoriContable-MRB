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
  MenuItem,
  IconButton,
  InputAdornment,
  Chip
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Search as SearchIcon, Inventory as InventoryIcon } from '@mui/icons-material';
import inventoryService, { Item } from '../../../services/inventoryService';
import { toast } from 'react-toastify';

const ProductsManager: React.FC = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [open, setOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  
  const [currentItem, setCurrentItem] = useState<Partial<Item>>({
    code: '',
    description: '',
    unit_price: 0,
    type: 'SERVICIO',
    tax_type: 'IVA_19',
    is_active: true
  });

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async (search = '') => {
    try {
      setLoading(true);
      const data = await inventoryService.getItems(search);
      setItems(Array.isArray(data) ? data : data.results);
    } catch (error) {
      console.error(error);
      toast.error('Error cargando inventario');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadItems(searchTerm);
  };

  const handleOpen = (item?: Item) => {
    if (item) {
      setCurrentItem(item);
      setIsEditing(true);
    } else {
      setCurrentItem({
        code: '',
        description: '',
        unit_price: 0,
        type: 'SERVICIO',
        tax_type: 'IVA_19',
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
      if (!currentItem.code || !currentItem.description) {
        toast.warning('Código y Descripción son obligatorios');
        return;
      }

      if (isEditing && currentItem.id) {
        await inventoryService.updateItem(currentItem.id, currentItem as Item);
        toast.success('Producto actualizado');
      } else {
        await inventoryService.createItem(currentItem as Item);
        toast.success('Producto creado');
      }
      handleClose();
      loadItems(searchTerm);
    } catch (error) {
      console.error(error);
      toast.error('Error guardando producto');
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(amount);
  };

  const getTaxLabel = (taxType: string) => {
    switch(taxType) {
        case 'IVA_19': return 'IVA 19%';
        case 'IVA_5': return 'IVA 5%';
        case 'EXENTO': return 'Exento';
        case 'EXCLUIDO': return 'Excluido';
        default: return taxType;
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InventoryIcon /> Maestro de Productos y Servicios
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()}>
          Nuevo Item
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
             <TextField 
                size="small" 
                fullWidth 
                placeholder="Buscar por código o descripción..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                    startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment>
                }}
             />
             <Button type="submit" variant="outlined">Buscar</Button>
        </form>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Código</TableCell>
              <TableCell>Descripción</TableCell>
              <TableCell>Tipo</TableCell>
              <TableCell align="right">Precio Venta</TableCell>
              <TableCell>Impuesto</TableCell>
              <TableCell align="center">Estado</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id} hover>
                <TableCell sx={{ fontWeight: 'bold' }}>{item.code}</TableCell>
                <TableCell>{item.description}</TableCell>
                <TableCell>
                    <Chip 
                        label={item.type} 
                        color={item.type === 'SERVICIO' ? 'info' : 'secondary'} 
                        size="small" 
                        variant="outlined"
                    />
                </TableCell>
                <TableCell align="right">{formatCurrency(item.unit_price)}</TableCell>
                <TableCell>{getTaxLabel(item.tax_type)}</TableCell>
                <TableCell align="center">
                    {item.is_active ? <Chip label="Activo" color="success" size="small" /> : <Chip label="Inactivo" size="small" />}
                </TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => handleOpen(item)} size="small"><EditIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
                <TableRow>
                    <TableCell colSpan={7} align="center">No hay productos registrados.</TableCell>
                </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
        <DialogTitle>{isEditing ? 'Editar Producto/Servicio' : 'Nuevo Producto/Servicio'}</DialogTitle>
        <DialogContent dividers>
          <Box display="flex" flexDirection="column" gap={2}>
            
            <Box display="flex" gap={2}>
                <TextField
                    label="Código"
                    value={currentItem.code}
                    onChange={(e) => setCurrentItem({ ...currentItem, code: e.target.value })}
                    required
                    fullWidth
                    helperText="Ej: SER-001"
                />
                <TextField
                    select
                    label="Tipo"
                    value={currentItem.type}
                    onChange={(e) => setCurrentItem({ ...currentItem, type: e.target.value as any })}
                    fullWidth
                >
                    <MenuItem value="PRODUCTO">Producto (Bien)</MenuItem>
                    <MenuItem value="SERVICIO">Servicio</MenuItem>
                </TextField>
            </Box>

            <TextField
              label="Descripción"
              value={currentItem.description}
              onChange={(e) => setCurrentItem({ ...currentItem, description: e.target.value })}
              required
              fullWidth
              multiline
              rows={2}
            />
            
            <Box display="flex" gap={2}>
                <TextField
                    label="Precio de Venta"
                    type="number"
                    value={currentItem.unit_price}
                    onChange={(e) => setCurrentItem({ ...currentItem, unit_price: parseFloat(e.target.value) })}
                    required
                    fullWidth
                    InputProps={{
                        startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    }}
                />
                <TextField
                    select
                    label="Tipo de Impuesto"
                    value={currentItem.tax_type}
                    onChange={(e) => setCurrentItem({ ...currentItem, tax_type: e.target.value as any })}
                    fullWidth
                >
                    <MenuItem value="IVA_19">IVA General 19%</MenuItem>
                    <MenuItem value="IVA_5">IVA Reducido 5%</MenuItem>
                    <MenuItem value="EXENTO">Exento (0%)</MenuItem>
                    <MenuItem value="EXCLUIDO">Excluido (Sin IVA)</MenuItem>
                </TextField>
            </Box>

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

export default ProductsManager;
