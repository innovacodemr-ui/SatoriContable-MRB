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
  Autocomplete,
  Divider,
  MenuItem,
  Checkbox,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import { Save as SaveIcon, ArrowBack as ArrowBackIcon, Search as SearchIcon } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import treasuryService, { BankAccount, PaymentOut, PaymentOutDetail } from '../../../services/treasuryService';
import purchasesService, { Supplier } from '../../../services/purchasesService';

const PaymentForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  
  // Catalogs
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [bankAccounts, setBankAccounts] = useState<BankAccount[]>([]);
  
  // Form State
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | null>(null);
  const [selectedBank, setSelectedBank] = useState<BankAccount | null>(null);
  const [paymentMethod, setPaymentMethod] = useState('TRANSFERENCIA');
  const [notes, setNotes] = useState('');
  
  // Details
  const [details, setDetails] = useState<PaymentOutDetail[]>([]);
  
  // Modal Selection
  const [openModal, setOpenModal] = useState(false);
  const [pendingInvoices, setPendingInvoices] = useState<any[]>([]); // ReceivedInvoices
  const [selectedInvoices, setSelectedInvoices] = useState<number[]>([]); // IDs

  useEffect(() => {
    loadCatalogs();
    if (id) {
        loadPayment(Number(id));
    }
  }, [id]);

  const loadCatalogs = async () => {
    try {
      const [suppliersData, banksData] = await Promise.all([
        purchasesService.getSuppliers(),
        treasuryService.getBankAccounts()
      ]);
      setSuppliers(Array.isArray(suppliersData) ? suppliersData : suppliersData.results);
      setBankAccounts(Array.isArray(banksData) ? banksData : banksData.results);
    } catch (error) {
      console.error("Error loading catalogs", error);
    }
  };

  const loadPayment = async (paymentId: number) => {
      // TODO: Implement load logic for viewing/editing
      // For now MVP Create Only
  };

  const handleOpenInvoiceSelector = async () => {
    if (!selectedSupplier) {
        alert("Seleccione un proveedor primero.");
        return;
    }
    setLoading(true);
    try {
        const allInvoices = await treasuryService.getPendingInvoices();
        const list = Array.isArray(allInvoices) ? allInvoices : allInvoices.results;
        
        // Filter mainly on frontend for MVP if backend doesn't support complex filtering yet
        // Assuming issuer_name might match supplier name or we rely on user filtering visually
        // For strict correctness, we'd filter by NIT/ID.
        // Assuming `issuer_name` is available on invoice and `name` on supplier.
        const filtered = list; // .filter((inv: any) => inv.issuer_name?.includes(selectedSupplier.name));
        
        setPendingInvoices(filtered);
        setOpenModal(true);
    } catch (error) {
        console.error("Error fetching invoices", error);
    } finally {
        setLoading(false);
    }
  };

  const handleAddSelectedInvoices = () => {
    const newDetails: PaymentOutDetail[] = [];
    selectedInvoices.forEach(invId => {
        const invoice = pendingInvoices.find(inv => inv.id === invId);
        if (invoice) {
            // Check if already added
            if (!details.some(d => d.invoice === invId)) {
                newDetails.push({
                    invoice: invoice.id,
                    invoice_number: invoice.invoice_number,
                    amount_paid: Number(invoice.total_amount) // Default to full pay
                });
            }
        }
    });
    setDetails([...details, ...newDetails]);
    setOpenModal(false);
    setSelectedInvoices([]);
  };

  const handleAmountChange = (index: number, value: string) => {
    const newDetails = [...details];
    newDetails[index].amount_paid = Number(value);
    setDetails(newDetails);
  };

  const handleRemoveDetail = (index: number) => {
    const newDetails = [...details];
    newDetails.splice(index, 1);
    setDetails(newDetails);
  };

  const totalAmount = details.reduce((sum, d) => sum + d.amount_paid, 0);

  const handleSave = async () => {
    if (!selectedSupplier || !selectedBank) {
        alert("Complete los campos obligatorios (Proveedor, Banco).");
        return;
    }
    if (details.length === 0) {
        alert("Seleccione al menos una factura para pagar.");
        return;
    }

    try {
        setLoading(true);
        const payload: PaymentOut = {
            payment_date: paymentDate,
            third_party: selectedSupplier.name, // Sending Name as per model charfield
            bank_account: selectedBank.id!,
            payment_method: paymentMethod,
            total_amount: totalAmount,
            notes: notes,
            details: details
        };

        const created = await treasuryService.createPayment(payload);
        
        // Auto-Post if requested? Prompt says "Guardar y Contabilizar"
        if (window.confirm("Comprobante Guardado. ¿Desea CONTABILIZARLO ahora? (Esto generará el asiento)")) {
            await treasuryService.postPayment(created.id);
            alert("Pago Contabilizado Exitosamente!");
        } else {
            alert("Pago guardado en borrador.");
        }
        
        navigate('/treasury/payments');
    } catch (error) {
        console.error("Error saving payment", error);
        alert("Error al guardar el pago.");
    } finally {
        setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/treasury/payments')}>
          Volver
        </Button>
        <Typography variant="h4">Nuevo Comprobante de Egreso</Typography>
      </Box>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
            <Grid item xs={12} md={3}>
                <TextField
                    label="Fecha de Pago"
                    type="date"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    value={paymentDate}
                    onChange={(e) => setPaymentDate(e.target.value)}
                />
            </Grid>
            <Grid item xs={12} md={5}>
                <Autocomplete
                    options={suppliers}
                    getOptionLabel={(option) => option.name || 'Desconocido'}
                    value={selectedSupplier}
                    onChange={(_, val) => setSelectedSupplier(val)}
                    renderInput={(params) => <TextField {...params} label="Proveedor" />}
                />
            </Grid>
            <Grid item xs={12} md={4}>
                <TextField
                    select
                    label="Cuenta Bancaria (Origen)"
                    fullWidth
                    value={selectedBank ? selectedBank.id : ''}
                    onChange={(e) => {
                        const bank = bankAccounts.find(b => b.id === Number(e.target.value));
                        setSelectedBank(bank || null);
                    }}
                >
                    {bankAccounts.map((bank) => (
                        <MenuItem key={bank.id} value={bank.id}>
                            {bank.bank_name} - {bank.name} ({bank.currency})
                        </MenuItem>
                    ))}
                </TextField>
            </Grid>
            <Grid item xs={12} md={4}>
                 <TextField
                    select
                    label="Método de Pago"
                    fullWidth
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                >
                    <MenuItem value="TRANSFERENCIA">Transferencia Bancaria</MenuItem>
                    <MenuItem value="CHEQUE">Cheque</MenuItem>
                    <MenuItem value="EFECTIVO">Efectivo</MenuItem>
                </TextField>
            </Grid>
            <Grid item xs={12} md={8}>
                <TextField
                    label="Observaciones / Notas"
                    fullWidth
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                />
            </Grid>
        </Grid>
      </Paper>

      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
         <Typography variant="h6">Facturas a Pagar</Typography>
         <Button 
            variant="outlined" 
            startIcon={<SearchIcon />} 
            onClick={handleOpenInvoiceSelector}
            disabled={!selectedSupplier}
         >
            Buscar Facturas Pendientes
         </Button>
      </Box>

      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table>
            <TableHead>
                <TableRow>
                     <TableCell>Factura N°</TableCell>
                     <TableCell align="right">Monto a Pagar</TableCell>
                     <TableCell align="right">Acciones</TableCell>
                </TableRow>
            </TableHead>
            <TableBody>
                {details.map((detail, index) => (
                    <TableRow key={index}>
                        <TableCell>{detail.invoice_number || `ID: ${detail.invoice}`}</TableCell>
                        <TableCell align="right" width="200">
                             <TextField
                                type="number"
                                size="small"
                                fullWidth
                                value={detail.amount_paid}
                                onChange={(e) => handleAmountChange(index, e.target.value)}
                                InputProps={{ startAdornment: '$' }}
                             />
                        </TableCell>
                        <TableCell align="right">
                             <Button color="error" onClick={() => handleRemoveDetail(index)}>
                                Quitar
                             </Button>
                        </TableCell>
                    </TableRow>
                ))}
                <TableRow>
                    <TableCell align="right"><strong>Total:</strong></TableCell>
                    <TableCell align="right">
                        <Typography variant="h6">
                            {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(totalAmount)}
                        </Typography>
                    </TableCell>
                    <TableCell></TableCell>
                </TableRow>
            </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
         <Button variant="outlined" onClick={() => navigate('/treasury/payments')}>Cancelar</Button>
         <Button variant="contained" size="large" onClick={handleSave} disabled={loading} startIcon={<SaveIcon />}>
            Guardar y Contabilizar
         </Button>
      </Box>

      {/* Modal Selector de Facturas */}
      <Dialog open={openModal} onClose={() => setOpenModal(false)} maxWidth="md" fullWidth>
         <DialogTitle>Seleccionar Facturas de {selectedSupplier?.name}</DialogTitle>
         <DialogContent>
            <TableContainer>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell padding="checkbox"></TableCell>
                            <TableCell>Factura</TableCell>
                            <TableCell>Fecha</TableCell>
                            <TableCell align="right">Total Original</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {pendingInvoices.map((inv) => (
                             <TableRow key={inv.id} hover onClick={() => {
                                 const selected = selectedInvoices.includes(inv.id);
                                 if (selected) setSelectedInvoices(selectedInvoices.filter(id => id !== inv.id));
                                 else setSelectedInvoices([...selectedInvoices, inv.id]);
                             }}>
                                <TableCell padding="checkbox">
                                    <Checkbox checked={selectedInvoices.includes(inv.id)} />
                                </TableCell>
                                <TableCell>{inv.invoice_number} - {inv.issuer_name}</TableCell>
                                <TableCell>{inv.issue_date}</TableCell>
                                <TableCell align="right">
                                    {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(inv.total_amount))}
                                </TableCell>
                             </TableRow>
                        ))}
                        {pendingInvoices.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} align="center">No se encontraron facturas.</TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
         </DialogContent>
         <DialogActions>
             <Button onClick={() => setOpenModal(false)}>Cancelar</Button>
             <Button onClick={handleAddSelectedInvoices} variant="contained">Agregar Seleccionadas</Button>
         </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PaymentForm;
