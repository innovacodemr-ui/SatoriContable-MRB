import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Autocomplete,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import { Delete as DeleteIcon, Save as SaveIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import purchasesService, { Supplier, SupportDocument, SupportDocumentItem } from '../../services/purchasesService';

const SupportDocumentForm: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  
  // Form State
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [issueDate, setIssueDate] = useState(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState(new Date().toISOString().split('T')[0]);
  const [items, setItems] = useState<SupportDocumentItem[]>([]);
  
  // New Item State
  const [newItem, setNewItem] = useState<SupportDocumentItem>({
    description: '',
    quantity: 1,
    unit_price: 0,
    total_amount: 0
  });

  useEffect(() => {
    loadSuppliers();
  }, []);

  const loadSuppliers = async () => {
    try {
      const data = await purchasesService.getSuppliers();
      setSuppliers(Array.isArray(data) ? data : data.results);
    } catch (error) {
      console.error("Error loading suppliers", error);
    }
  };

  const handleAddItem = () => {
    if (!newItem.description || newItem.quantity <= 0 || newItem.unit_price <= 0) {
      alert("Por favor complete los datos del ítem.");
      return;
    }
    const total = newItem.quantity * newItem.unit_price;
    setItems([...items, { ...newItem, total_amount: total }]);
    setNewItem({ description: '', quantity: 1, unit_price: 0, total_amount: 0 });
  };

  const handleRemoveItem = (index: number) => {
    const newItems = [...items];
    newItems.splice(index, 1);
    setItems(newItems);
  };

  const calculateTotals = () => {
    const subtotal = items.reduce((sum, item) => sum + item.total_amount, 0);
    // Simplified Tax logic. Real logic might allow selecting tax per item.
    // Assuming 0 tax for Support Document MVP unless specified otherwise.
    // Or maybe we should allow adding tax? The Prompt says 'Retenciones' but usually Support Document
    // is for non-taxpayers, thus mostly 0 VAT, but Retentions apply.
    // Retentions are usually deducted. 
    // For simplicity, let's keep retentions 0 visible but not editable yet? 
    // Or just simple total = subtotal for now as prompt just asked for visual structure.
    
    return {
      subtotal,
      retentions: 0,
      total: subtotal // - retentions
    };
  };

  const totals = calculateTotals();

  const handleSave = async () => {
    if (!selectedSupplier) {
      alert("Seleccione un proveedor");
      return;
    }
    if (items.length === 0) {
      alert("Agregue al menos un ítem");
      return;
    }

    try {
      setLoading(true);
      const payload: SupportDocument = {
        issue_date: issueDate,
        due_date: dueDate,
        supplier: selectedSupplier.id,
        items: items,
        subtotal: totals.subtotal,
        tax_amount: 0,
        total_amount: totals.total
      };

      await purchasesService.createSupportDocument(payload);
      alert("Documento guardado exitosamente");
      navigate('/purchases/support-documents');
    } catch (error) {
      console.error("Error creating document", error);
      alert("Error al guardar documento");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/purchases/support-documents')}>
          Volver
        </Button>
        <Typography variant="h4">Nuevo Documento Soporte</Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Cabecera */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Autocomplete
                    options={suppliers}
                    getOptionLabel={(option) => option.name || 'Sin Nombre'}
                    value={selectedSupplier}
                    onChange={(_, value) => setSelectedSupplier(value)}
                    renderInput={(params) => <TextField {...params} label="Proveedor" fullWidth />}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField
                    label="Fecha Emisión"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={issueDate}
                    onChange={(e) => setIssueDate(e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} md={3}>
                  <TextField
                    label="Fecha Vencimiento"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                  />
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Detalle */}
        <Grid item xs={12}>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell width="40%">Descripción</TableCell>
                  <TableCell width="15%" align="right">Cantidad</TableCell>
                  <TableCell width="20%" align="right">Precio Unitario</TableCell>
                  <TableCell width="20%" align="right">Total</TableCell>
                  <TableCell width="5%"></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {/* Input Row */}
                <TableRow sx={{ bgcolor: '#f5f5f5' }}>
                  <TableCell>
                    <TextField
                      placeholder="Descripción del servicio/producto"
                      fullWidth
                      size="small"
                      value={newItem.description}
                      onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <TextField
                      type="number"
                      size="small"
                      fullWidth
                      value={newItem.quantity}
                      onChange={(e) => setNewItem({ ...newItem, quantity: Number(e.target.value) })}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <TextField
                      type="number"
                      size="small"
                      fullWidth
                      value={newItem.unit_price}
                      onChange={(e) => setNewItem({ ...newItem, unit_price: Number(e.target.value) })}
                    />
                  </TableCell>
                  <TableCell align="right">
                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(newItem.quantity * newItem.unit_price)}
                  </TableCell>
                  <TableCell>
                    <Button variant="contained" size="small" onClick={handleAddItem}>
                      Agregar
                    </Button>
                  </TableCell>
                </TableRow>

                {/* Items List */}
                {items.map((item, index) => (
                  <TableRow key={index}>
                    <TableCell>{item.description}</TableCell>
                    <TableCell align="right">{item.quantity}</TableCell>
                    <TableCell align="right">
                      {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(item.unit_price)}
                    </TableCell>
                    <TableCell align="right">
                      {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(item.total_amount)}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" color="error" onClick={() => handleRemoveItem(index)}>
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Grid>

        {/* Totales */}
        <Grid item xs={12}>
           <Box display="flex" justifyContent="flex-end">
             <Card sx={{ minWidth: 300 }}>
               <CardContent>
                 <Box display="flex" justifyContent="space-between" mb={1}>
                   <Typography>Subtotal:</Typography>
                   <Typography>{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(totals.subtotal)}</Typography>
                 </Box>
                 {/* 
                 <Box display="flex" justifyContent="space-between" mb={1}>
                   <Typography>Retenciones:</Typography>
                   <Typography color="error">-{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(totals.retentions)}</Typography>
                 </Box>
                 */}
                 <Divider sx={{ my: 1 }} />
                 <Box display="flex" justifyContent="space-between">
                   <Typography variant="h6">Total a Pagar:</Typography>
                   <Typography variant="h6" color="primary">
                     {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(totals.total)}
                   </Typography>
                 </Box>
               </CardContent>
             </Card>
           </Box>
        </Grid>

        <Grid item xs={12}>
          <Box display="flex" justifyContent="flex-end" gap={2}>
            <Button variant="outlined" onClick={() => navigate('/purchases/support-documents')}> Cancelar </Button>
            <Button variant="contained" color="primary" size="large" onClick={handleSave} disabled={loading} startIcon={<SaveIcon />}>
              {loading ? 'Guardando...' : 'Guardar Documento'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SupportDocumentForm;
