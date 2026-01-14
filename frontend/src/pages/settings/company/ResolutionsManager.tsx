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
  FormControl,
  InputLabel,
  Select,
  IconButton
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import invoicingService, { Resolution } from '../../../services/invoicingService';
import { toast } from 'react-toastify';

const ResolutionsManager: React.FC = () => {
  const [resolutions, setResolutions] = useState<Resolution[]>([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [currentResolution, setCurrentResolution] = useState<Partial<Resolution>>({
    name: 'Resolución de Facturación 2026',
    doc_type: 'INVOICE',
    prefix: 'FE',
    number: '',
    start_range: 1,
    end_range: 10000,
    current_number: 1,
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
    technical_key: '',
    is_active: true
  });
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadResolutions();
  }, []);

  const loadResolutions = async () => {
    try {
      setLoading(true);
      const data = await invoicingService.getResolutions();
      setResolutions(Array.isArray(data) ? data : data.results); // handled paged response
    } catch (error) {
      console.error(error);
      toast.error('Error cargando resoluciones');
    } finally {
      setLoading(false);
    }
  };

  const handleOpen = (resolution?: Resolution) => {
    if (resolution) {
      setCurrentResolution(resolution);
      setIsEditing(true);
    } else {
        // Reset form
      setCurrentResolution({
            name: 'Resolución de Facturación 2026',
            doc_type: 'INVOICE',
            prefix: 'FE',
            number: '',
            start_range: 1,
            end_range: 10000,
            current_number: 1,
            start_date: new Date().toISOString().split('T')[0],
            end_date: new Date().toISOString().split('T')[0],
            technical_key: '',
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
      if (isEditing && currentResolution.id) {
        await invoicingService.updateResolution(currentResolution.id, currentResolution as Resolution);
        toast.success('Resolución actualizada');
      } else {
        await invoicingService.createResolution(currentResolution as Resolution);
        toast.success('Resolución creada');
      }
      handleClose();
      loadResolutions();
    } catch (error) {
      console.error(error);
      toast.error('Error guardando resolución');
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">Resoluciones DIAN</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpen()}>
          Nueva Resolución
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Tipo</TableCell>
              <TableCell>Resolución</TableCell>
              <TableCell>Prefijo</TableCell>
              <TableCell>Rango</TableCell>
              <TableCell>Vigencia</TableCell>
              <TableCell>Actual</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {resolutions.map((res) => (
              <TableRow key={res.id}>
                <TableCell>{res.doc_type === 'INVOICE' ? 'Facelec' : 'Doc. Soporte'}</TableCell>
                <TableCell>
                  <Typography variant="body2" fontWeight="bold">{res.number}</Typography>
                  <Typography variant="caption">{res.name}</Typography>
                </TableCell>
                <TableCell>{res.prefix}</TableCell>
                <TableCell>{res.start_range} - {res.end_range}</TableCell>
                <TableCell>{res.end_date}</TableCell>
                <TableCell>{res.current_number}</TableCell>
                <TableCell>{res.is_active ? 'Activa' : 'Inactiva'}</TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => handleOpen(res)}><EditIcon /></IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>{isEditing ? 'Editar Resolución' : 'Nueva Resolución'}</DialogTitle>
        <DialogContent dividers>
          <Box display="flex" flexDirection="column" gap={2}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Documento</InputLabel>
              <Select
                value={currentResolution.doc_type}
                label="Tipo de Documento"
                onChange={(e) => setCurrentResolution({ ...currentResolution, doc_type: e.target.value as any })}
              >
                <MenuItem value="INVOICE">Factura Electrónica de Venta</MenuItem>
                <MenuItem value="SUPPORT_DOC">Documento Soporte</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Número/Nombre Resolución"
              fullWidth
              value={currentResolution.number}
              onChange={(e) => setCurrentResolution({ ...currentResolution, number: e.target.value })}
              helperText="Ej: 18760000001"
            />
            
            <TextField
              label="Nombre Descriptivo"
              fullWidth
              value={currentResolution.name}
              onChange={(e) => setCurrentResolution({ ...currentResolution, name: e.target.value })}
            />

            <Box display="flex" gap={2}>
              <TextField
                label="Prefijo"
                value={currentResolution.prefix}
                onChange={(e) => setCurrentResolution({ ...currentResolution, prefix: e.target.value })}
              />
              <TextField
                label="Desde"
                type="number"
                fullWidth
                value={currentResolution.start_range}
                onChange={(e) => setCurrentResolution({ ...currentResolution, start_range: parseInt(e.target.value) })}
              />
              <TextField
                label="Hasta"
                type="number"
                fullWidth
                value={currentResolution.end_range}
                onChange={(e) => setCurrentResolution({ ...currentResolution, end_range: parseInt(e.target.value) })}
              />
            </Box>

            <Box display="flex" gap={2}>
               <TextField
                label="Consecutivo Actual"
                type="number"
                fullWidth
                helperText="Siguiente número a usar"
                value={currentResolution.current_number}
                onChange={(e) => setCurrentResolution({ ...currentResolution, current_number: parseInt(e.target.value) })}
              />
              <TextField
                label="Fecha Inicio"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={currentResolution.start_date}
                onChange={(e) => setCurrentResolution({ ...currentResolution, start_date: e.target.value })}
              />
              <TextField
                label="Fecha Vencimiento"
                type="date"
                fullWidth
                InputLabelProps={{ shrink: true }}
                value={currentResolution.end_date}
                onChange={(e) => setCurrentResolution({ ...currentResolution, end_date: e.target.value })}
              />
            </Box>

            <TextField
              label="Clave Técnica DIAN"
              fullWidth
              type="password"
              value={currentResolution.technical_key}
              onChange={(e) => setCurrentResolution({ ...currentResolution, technical_key: e.target.value })}
              helperText="Requerido para firmar facturas (Cópialo del portal DIAN)"
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

export default ResolutionsManager;
