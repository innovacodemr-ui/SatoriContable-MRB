import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Stack
} from '@mui/material';
import { payrollService } from '../../services/api';
import { format } from 'date-fns';

interface PayrollResult {
  employee: string;
  document_id: number;
  employee_name: string;
  position: string;
  net: number;
  worked_days: number;
  novelty_days: number;
  accrued: number;
  deductions: number;
  dian_status: string;
}

interface Period {
  id: number;
  name: string;
  status: string;
}

const PayrollDashboard: React.FC = () => {
  const [periods, setPeriods] = useState<Period[]>([]);
  const [selectedPeriod, setSelectedPeriod] = useState<number | ''>('');
  const [results, setResults] = useState<PayrollResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [liquidating, setLiquidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Estado para el diálogo de crear periodo
  const [openDialog, setOpenDialog] = useState(false);
  const [newPeriodData, setNewPeriodData] = useState({
      name: '',
      start_date: '',
      end_date: '',
      payment_date: ''
  });

  useEffect(() => {
    loadPeriods();
  }, []);

  const loadPeriods = async () => {
    try {
      setLoading(true);
      const data = await payrollService.getPeriods();
      setPeriods(data.results || data);
      
      // Auto-select first active period if available
      if (data.results && data.results.length > 0) {
          // Logic could be improved to select "current"
      }
    } catch (err) {
      setError("Error cargando periodos.");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenCreatePeriod = () => {
      // Pre-llenar con fechas sugeridas (mes actual) pero permitir edición
      const now = new Date();
      const startOfMonth = format(new Date(now.getFullYear(), now.getMonth(), 1), 'yyyy-MM-dd');
      const endOfMonth = format(new Date(now.getFullYear(), now.getMonth() + 1, 0), 'yyyy-MM-dd');
      
      setNewPeriodData({
          name: '',
          start_date: startOfMonth,
          end_date: endOfMonth,
          payment_date: endOfMonth
      });
      setOpenDialog(true);
  };

  const handleSavePeriod = async () => {
    if (!newPeriodData.name || !newPeriodData.start_date || !newPeriodData.end_date) {
        alert("Por favor complete los campos obligatorios");
        return;
    }

    try {
        setLoading(true);
        const newPeriod = await payrollService.createPeriod({
            ...newPeriodData,
            status: "DRAFT"
        });
        setPeriods([...periods, newPeriod]);
        setSelectedPeriod(newPeriod.id);
        setOpenDialog(false);
        setError(null);
    } catch (err: any) {
        setError("Error creando periodo: " + (err.response?.data?.error || err.message));
    } finally {
        setLoading(false);
    }
  };

  const handleLiquidate = async () => {
    // If no period selected, try to use the last one created
    const targetPeriod = selectedPeriod || (periods.length > 0 ? periods[periods.length - 1].id : null);
    
    if (!targetPeriod) {
        setError("Seleccione un periodo para liquidar.");
        return;
    }
    
    setLiquidating(true);
    setError(null);
    try {
      const response = await payrollService.liquidatePeriod(Number(targetPeriod));
      setResults(response.results);
    } catch (err: any) {
      console.error(err);
      setError("Error al liquidar nómina. " + (err.response?.data?.error || err.message));
    } finally {
      setLiquidating(false);
    }
  };

  const handleDownload = async (docId: number, employeeName: string) => {
      try {
          const blob = await payrollService.downloadPayslip(docId);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.style.display = 'none';
          a.href = url;
          a.download = `Nomina_${employeeName}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
      } catch (err) {
          console.error(err);
          alert("Error descargando desprendible.");
      }
  };

  const handleTransmit = async (docId: number) => {
    if (!window.confirm('¿Transmitir este documento a la DIAN?')) return;
    try {
        await payrollService.transmitDocument(docId);
        alert('Documento enviado a validación');
        // Refresh
        handleLiquidate(); 
    } catch (err) {
        console.error('Error transmitiendo:', err);
        alert('Error transmitiendo documento a la DIAN');
    }
  };

  const statusBadge = (status: string) => {
    // Map backend status to frontend labels/colors
    const statusMap: {[key: string]: string} = {
      'PENDING': 'BORRADOR',
      'DRAFT': 'BORRADOR',
      'BORRADOR': 'BORRADOR',
      'SENT': 'ENVIADO',
      'ACCEPTED': 'ACEPTADO',
      'REJECTED': 'RECHAZADO'
    };
    
    const displayStatus = statusMap[status] || status || 'BORRADOR';

    const colors: {[key: string]: 'default' | 'primary' | 'success' | 'error' | 'warning'} = {
      'BORRADOR': 'default',
      'ENVIADO': 'primary',
      'ACEPTADO': 'success',
      'RECHAZADO': 'error',
      'FALLIDO': 'error'
    };
    return (
      <Chip 
        label={displayStatus} 
        color={colors[displayStatus] || 'default'} 
        size="small" 
        variant="outlined" 
      />
    );
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Centro de Control de Nómina
      </Typography>

      {/* Toolbar */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
             <FormControl fullWidth size="small">
                 <InputLabel>Periodo de Liquidación</InputLabel>
                 <Select
                    value={selectedPeriod}
                    label="Periodo de Liquidación"
                    onChange={(e) => setSelectedPeriod(Number(e.target.value))}
                 >
                     {periods.map(p => (
                         <MenuItem key={p.id} value={p.id}>
                             {p.name} ({p.status})
                         </MenuItem>
                     ))}
                 </Select>
             </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
              <Button onClick={handleOpenCreatePeriod} variant="outlined">
                  + Crear Nuevo Periodo
              </Button>
          </Grid>
          <Grid item xs={12} md={4} sx={{ textAlign: 'right' }}>
              <Button 
                variant="contained" 
                color="error" 
                size="large"
                onClick={handleLiquidate}
                disabled={!selectedPeriod || liquidating}
              >
                  {liquidating ? <CircularProgress size={24} color="inherit" /> : "LIQUIDAR NÓMINA"}
              </Button>
          </Grid>
        </Grid>
      </Paper>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

      {/* Results Grid */}
      {results.length > 0 && (
          <TableContainer component={Paper}>
              <Table>
                  <TableHead>
                      <TableRow>
                          <TableCell>Empleado</TableCell>
                          <TableCell>Tiempo</TableCell>
                          <TableCell align="right">Devengado</TableCell>
                          <TableCell align="right">Deducciones</TableCell>
                          <TableCell align="right">Neto a Pagar</TableCell>
                          <TableCell>Estado</TableCell>
                          <TableCell>Acciones</TableCell>
                      </TableRow>
                  </TableHead>
                  <TableBody>
                      {results.map((row) => (
                          <TableRow key={row.employee}>
                              <TableCell>
                                  <Typography variant="subtitle2">{row.employee_name}</Typography>
                                  <Typography variant="caption" color="textSecondary">{row.position}</Typography>
                              </TableCell>
                              <TableCell>
                                  {row.worked_days > 0 && (
                                     <Chip label={`${row.worked_days} días Trab.`} color="primary" variant="outlined" size="small" sx={{ mr: 1 }} />
                                  )}
                                  {row.novelty_days > 0 && (
                                      <Chip label={`${row.novelty_days} días Nov.`} color="warning" size="small" />
                                  )}
                              </TableCell>
                              <TableCell align="right" sx={{ color: 'green' }}>
                                  {formatCurrency(row.accrued)}
                              </TableCell>
                              <TableCell align="right" sx={{ color: 'red' }}>
                                  {formatCurrency(row.deductions)}
                              </TableCell>
                              <TableCell align="right">
                                  <Typography variant="subtitle1" fontWeight="bold">
                                      {formatCurrency(row.net)}
                                  </Typography>
                              </TableCell>
                              <TableCell>
                                  {statusBadge(row.dian_status)}
                              </TableCell>
                              <TableCell>
                                  <Button 
                                      size="small" 
                                      variant="outlined" 
                                      onClick={() => handleDownload(row.document_id, row.employee_name)}
                                      sx={{ mr: 1 }}
                                  >
                                      Imprimir
                                  </Button>
                                  {(row.dian_status === 'BORRADOR' || row.dian_status === 'PENDING' || row.dian_status === 'RECHAZADO') && (
                                    <Button 
                                        size="small" 
                                        variant="contained" 
                                        color="primary"
                                        onClick={() => handleTransmit(row.document_id)}
                                    >
                                        Transmitir
                                    </Button>
                                  )}
                              </TableCell>
                          </TableRow>
                      ))}
                  </TableBody>
              </Table>
          </TableContainer>
      )}
      
      {results.length === 0 && !loading && (
          <Box sx={{ textAlign: 'center', mt: 5, color: 'text.secondary' }}>
              <Typography>Seleccione un periodo y haga clic en Liquidar para ver resultados.</Typography>
          </Box>
      )}

      {/* Dialogo CREAR PERIODO */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Crear Nuevo Periodo de Nómina</DialogTitle>
        <DialogContent>
            <Stack spacing={2} sx={{ mt: 1 }}>
                <TextField 
                    label="Nombre del Periodo" 
                    placeholder="Ej: Enero 2026 - Quincena 1"
                    fullWidth 
                    value={newPeriodData.name}
                    onChange={(e) => setNewPeriodData({...newPeriodData, name: e.target.value})}
                />
                <TextField 
                    label="Fecha Inicio" 
                    type="date"
                    fullWidth 
                    InputLabelProps={{ shrink: true }}
                    value={newPeriodData.start_date}
                    onChange={(e) => setNewPeriodData({...newPeriodData, start_date: e.target.value})}
                />
                <TextField 
                    label="Fecha Fin" 
                    type="date"
                    fullWidth 
                    InputLabelProps={{ shrink: true }}
                    value={newPeriodData.end_date}
                    onChange={(e) => setNewPeriodData({...newPeriodData, end_date: e.target.value})}
                />
                <TextField 
                    label="Fecha Pago (Dispersión)" 
                    type="date"
                    fullWidth 
                    InputLabelProps={{ shrink: true }}
                    value={newPeriodData.payment_date}
                    onChange={(e) => setNewPeriodData({...newPeriodData, payment_date: e.target.value})}
                />
            </Stack>
        </DialogContent>
        <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>Cancelar</Button>
            <Button onClick={handleSavePeriod} variant="contained">Crear Periodo</Button>
        </DialogActions>
      </Dialog>


    </Box>
  );
};

export default PayrollDashboard;
