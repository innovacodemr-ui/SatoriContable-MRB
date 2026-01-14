import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Grid,
  TextField,
  MenuItem,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Autocomplete
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Save as SaveIcon } from '@mui/icons-material';
import invoicingService, { Resolution, Invoice, InvoiceLine } from '../../services/invoicingService';
import inventoryService, { Item } from '../../services/inventoryService';
import { thirdPartiesService } from '../../services/api'; 
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

const InvoiceForm: React.FC = () => {
  const navigate = useNavigate();
  const [resolutions, setResolutions] = useState<Resolution[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [invoiceData, setInvoiceData] = useState<Partial<Invoice>>({
    payment_term: 'CONTADO',
    payment_due_date: new Date().toISOString().split('T')[0],
    notes: '',
    lines: []
  });
  
  // Totals
  const [totals, setTotals] = useState({ subtotal: 0, tax: 0, total: 0 });

  useEffect(() => {
    loadDependencies();
  }, []);

  const loadDependencies = async () => {
    try {
      setLoading(true);
      const [resData, custData, itemsData] = await Promise.all([
        invoicingService.getResolutions(),
        thirdPartiesService.getAll({ party_type: 'CUSTOMER' }), // Assuming filter
        inventoryService.getItems()
      ]);
      setResolutions(Array.isArray(resData) ? resData : resData.results);
      setCustomers(Array.isArray(custData) ? custData : custData.results);
      setItems(Array.isArray(itemsData) ? itemsData : itemsData.results);

      // Default Resolution
      if (resData.length > 0) {
        setInvoiceData(prev => ({ ...prev, resolution: resData[0].id }));
      }
    } catch (error) {
      console.error(error);
      toast.error('Error cargando datos maestros');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLine = () => {
    setInvoiceData({
      ...invoiceData,
      lines: [...(invoiceData.lines || []), { 
          description: '', 
          quantity: 1, 
          unit_price: 0, 
          tax_rate: 19, 
          subtotal: 0, 
          tax_amount: 0, 
          total: 0 
      }]
    });
  };

  const handleRemoveLine = (index: number) => {
    const newLines = [...(invoiceData.lines || [])];
    newLines.splice(index, 1);
    setInvoiceData({ ...invoiceData, lines: newLines });
  };

  const handleLineChange = (index: number, field: keyof InvoiceLine, value: any) => {
    const newLines = [...(invoiceData.lines || [])];
    const line = { ...newLines[index], [field]: value };
    
    // Recalculate line totals
    let price = parseFloat(line.unit_price as any) || 0;
    let qty = parseFloat(line.quantity as any) || 0;
    let rate = parseFloat(line.tax_rate as any) || 0;
    
    line.subtotal = price * qty;
    line.tax_amount = line.subtotal * (rate / 100);
    line.total = line.subtotal + line.tax_amount;
    
    newLines[index] = line;
    setInvoiceData({ ...invoiceData, lines: newLines });
  };

  const handleProductSelect = (index: number, item: Item | null) => {
      if (!item) return;
      
      let taxRate = 19;
      if (item.tax_type === 'IVA_5') taxRate = 5;
      if (item.tax_type === 'EXENTO' || item.tax_type === 'EXCLUIDO') taxRate = 0;

      const newLines = [...(invoiceData.lines || [])];
      const line = { 
          ...newLines[index], 
          item: item.id,
          description: item.description,
          unit_price: item.unit_price,
          tax_rate: taxRate,
          quantity: 1
      };
      
      // Calculate
      line.subtotal = line.unit_price * line.quantity;
      line.tax_amount = line.subtotal * (line.tax_rate / 100);
      line.total = line.subtotal + line.tax_amount;

      newLines[index] = line;
      setInvoiceData({ ...invoiceData, lines: newLines });
  };

  useEffect(() => {
      // Calculate Global Totals
      const sub = (invoiceData.lines || []).reduce((acc, line) => acc + (line.subtotal || 0), 0);
      const tax = (invoiceData.lines || []).reduce((acc, line) => acc + (line.tax_amount || 0), 0);
      setTotals({ subtotal: sub, tax: tax, total: sub + tax });
  }, [invoiceData.lines]);

  const handleSubmit = async () => {
    if (!invoiceData.customer || !invoiceData.resolution || (invoiceData.lines || []).length === 0) {
        toast.warning('Complete los campos obligatorios y agregue al menos un producto');
        return;
    }
    
    try {
        await invoicingService.createInvoice(invoiceData as Invoice);
        toast.success('Factura creada exitosamente');
        navigate('/dian/documents'); // Go to list? Or stay?
    } catch (e) {
        console.error(e);
        toast.error('Error al guardar la factura');
    }
  };

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(val);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
         <Typography variant="h5">Nueva Factura de Venta</Typography>
         <Button variant="contained" startIcon={<SaveIcon />} onClick={handleSubmit}>
            Guardar y Emitir
         </Button>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
         <Grid container spacing={3}>
             <Grid item xs={12} md={6}>
                 <Autocomplete
                    options={customers}
                    getOptionLabel={(opt) => opt.business_name || `${opt.first_name} ${opt.surname}`}
                    onChange={(_, val) => setInvoiceData({ ...invoiceData, customer: val?.id })}
                    renderInput={(params) => <TextField {...params} label="Cliente" required />}
                 />
             </Grid>
             <Grid item xs={12} md={3}>
                 <TextField
                    select
                    label="Resolución"
                    fullWidth
                    value={invoiceData.resolution || ''}
                    onChange={(e) => setInvoiceData({ ...invoiceData, resolution: Number(e.target.value) })}
                    helperText={resolutions.find(r => r.id === invoiceData.resolution)?.prefix + ' - Actual: ' + resolutions.find(r => r.id === invoiceData.resolution)?.current_number}
                 >
                    {resolutions.map(r => (
                        <MenuItem key={r.id} value={r.id}>
                            {r.prefix} ({r.start_range}-{r.end_range})
                        </MenuItem>
                    ))}
                 </TextField>
             </Grid>
              <Grid item xs={12} md={3}>
                 <TextField
                    select
                    label="Plazo de Pago"
                    fullWidth
                    value={invoiceData.payment_term}
                    onChange={(e) => setInvoiceData({ ...invoiceData, payment_term: e.target.value })}
                 >
                     <MenuItem value="CONTADO">Contado</MenuItem>
                     <MenuItem value="30_DIAS">Crédito 30 Días</MenuItem>
                     <MenuItem value="60_DIAS">Crédito 60 Días</MenuItem>
                 </TextField>
             </Grid>
             <Grid item xs={12} md={3}>
                <TextField
                    type="date"
                    label="Fecha Vencimiento"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={invoiceData.payment_due_date}
                    onChange={(e) => setInvoiceData({ ...invoiceData, payment_due_date: e.target.value })}
                />
             </Grid>
         </Grid>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
            <TableHead>
                <TableRow>
                    <TableCell width="30%">Producto/Servicio</TableCell>
                    <TableCell width="10%">Cantidad</TableCell>
                    <TableCell width="15%">Precio Unit.</TableCell>
                    <TableCell width="10%">% IVA</TableCell>
                    <TableCell width="15%">Subtotal</TableCell>
                    <TableCell width="15%">Total</TableCell>
                    <TableCell width="5%"></TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {invoiceData.lines?.map((line, idx) => (
                    <TableRow key={idx}>
                        <TableCell>
                            <Autocomplete
                                options={items}
                                getOptionLabel={(opt) => `${opt.code} - ${opt.description}`}
                                onChange={(_, val) => handleProductSelect(idx, val)}
                                renderInput={(params) => <TextField {...params} placeholder="Buscar item..." variant="standard" />}
                            />
                            <TextField 
                                variant="standard" 
                                fullWidth 
                                value={line.description} 
                                onChange={(e) => handleLineChange(idx, 'description', e.target.value)}
                                placeholder="Descripción adicional"
                            />
                        </TableCell>
                        <TableCell>
                            <TextField
                                type="number"
                                value={line.quantity}
                                onChange={(e) => handleLineChange(idx, 'quantity', e.target.value)}
                                variant="standard"
                            />
                        </TableCell>
                        <TableCell>
                             <TextField
                                type="number"
                                value={line.unit_price}
                                onChange={(e) => handleLineChange(idx, 'unit_price', e.target.value)}
                                variant="standard"
                                InputProps={{ startAdornment: '$' }}
                            />
                        </TableCell>
                        <TableCell>
                            <TextField
                                type="number"
                                value={line.tax_rate}
                                onChange={(e) => handleLineChange(idx, 'tax_rate', e.target.value)}
                                variant="standard"
                            />
                        </TableCell>
                        <TableCell>{formatCurrency(line.subtotal || 0)}</TableCell>
                        <TableCell>{formatCurrency(line.total || 0)}</TableCell>
                        <TableCell>
                            <IconButton onClick={() => handleRemoveLine(idx)} color="error"><DeleteIcon /></IconButton>
                        </TableCell>
                    </TableRow>
                ))}
                <TableRow>
                    <TableCell colSpan={7}>
                        <Button startIcon={<AddIcon />} onClick={handleAddLine}>Agregar Línea</Button>
                    </TableCell>
                </TableRow>
            </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
          <Paper sx={{ p: 2, minWidth: 300 }}>
              <Grid container spacing={1}>
                  <Grid item xs={6}><Typography>Subtotal:</Typography></Grid>
                  <Grid item xs={6} textAlign="right"><Typography>{formatCurrency(totals.subtotal)}</Typography></Grid>
                  
                  <Grid item xs={6}><Typography>Impuestos:</Typography></Grid>
                  <Grid item xs={6} textAlign="right"><Typography>{formatCurrency(totals.tax)}</Typography></Grid>
                  
                  <Grid item xs={12}><Typography variant="h6" fontWeight="bold" align="right">Total: {formatCurrency(totals.total)}</Typography></Grid>
              </Grid>
          </Paper>
      </Box>

    </Box>
  );
};

export default InvoiceForm;
