import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, IconButton, Grid, Card, CardContent,
  CircularProgress, Alert, Tabs, Tab
} from '@mui/material';
import {
  Refresh as RefreshIcon, Visibility as ViewIcon, Payment as PaymentIcon
} from '@mui/icons-material';
import { isDesktop } from '../../services/api';
import { toast } from 'react-toastify';

interface AccountPayable {
  id: number;
  supplier_id: number;
  supplier_name: string;
  supplier_id_number: string;
  document_number: string;
  issue_date: string;
  due_date: string;
  total_amount: number;
  paid_amount: number;
  balance: number;
  status: string;
  days_overdue: number;
  description: string;
}

const AccountsPayable: React.FC = () => {
  const [payables, setPayables] = useState<AccountPayable[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    loadPayables();
  }, []);

  const loadPayables = async () => {
    setLoading(true);
    try {
      if (isDesktop()) {
        // Consulta SQL para obtener cuentas por pagar
        const result = await window.electronAPI!.dbQuery(`
          SELECT 
            je.id,
            tp.id as supplier_id,
            tp.name as supplier_name,
            tp.id_number as supplier_id_number,
            je.number as document_number,
            je.date as issue_date,
            date(je.date, '+30 days') as due_date,
            ABS(SUM(CASE WHEN jel.credit > 0 THEN jel.credit ELSE 0 END)) as total_amount,
            0 as paid_amount,
            ABS(SUM(CASE WHEN jel.credit > 0 THEN jel.credit ELSE 0 END)) as balance,
            CASE 
              WHEN julianday('now') - julianday(je.date) > 30 THEN 'VENCIDA'
              ELSE 'VIGENTE'
            END as status,
            CAST(MAX(0, julianday('now') - julianday(je.date, '+30 days')) AS INTEGER) as days_overdue,
            je.description
          FROM journal_entries je
          INNER JOIN journal_entry_lines jel ON je.id = jel.journal_entry_id
          INNER JOIN accounts a ON jel.account_id = a.id
          LEFT JOIN third_parties tp ON jel.third_party_id = tp.id
          WHERE a.code IN ('220505', '2335')  -- Proveedores y Costos por pagar
            AND jel.credit > 0
            AND je.status = 'POSTED'
            AND tp.is_supplier = 1
          GROUP BY je.id, tp.id, tp.name, tp.id_number, je.number, je.date, je.description
          ORDER BY je.date DESC
        `);
        
        if (result.success) {
          setPayables(result.data || []);
        }
      } else {
        // Llamada API para web
        toast.info('Función disponible próximamente en versión web');
      }
    } catch (error: any) {
      toast.error('Error al cargar cuentas por pagar');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotals = () => {
    const total = payables.reduce((sum, p) => sum + p.total_amount, 0);
    const paid = payables.reduce((sum, p) => sum + p.paid_amount, 0);
    const balance = payables.reduce((sum, p) => sum + p.balance, 0);
    const overdue = payables.filter(p => p.status === 'VENCIDA').reduce((sum, p) => sum + p.balance, 0);
    
    return { total, paid, balance, overdue };
  };

  const filteredPayables = payables.filter(p => {
    if (tabValue === 0) return true; // Todas
    if (tabValue === 1) return p.status === 'VIGENTE'; // Vigentes
    if (tabValue === 2) return p.status === 'VENCIDA'; // Vencidas
    return true;
  });

  const totals = calculateTotals();

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Cuentas por Pagar
        </Typography>
        <Box>
          {isDesktop() && (
            <Chip label="Modo Desktop" color="primary" size="small" sx={{ mr: 2 }} />
          )}
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadPayables}>
            Actualizar
          </Button>
        </Box>
      </Box>

      {/* Resumen */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Adeudado
              </Typography>
              <Typography variant="h5" color="primary">
                ${totals.total.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Pagado
              </Typography>
              <Typography variant="h5" color="success.main">
                ${totals.paid.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Saldo Pendiente
              </Typography>
              <Typography variant="h5" color="warning.main">
                ${totals.balance.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Deuda Vencida
              </Typography>
              <Typography variant="h5" color="error.main">
                ${totals.overdue.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Paper sx={{ p: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)} sx={{ mb: 2 }}>
          <Tab label={`Todas (${payables.length})`} />
          <Tab label={`Vigentes (${payables.filter(p => p.status === 'VIGENTE').length})`} />
          <Tab label={`Vencidas (${payables.filter(p => p.status === 'VENCIDA').length})`} />
        </Tabs>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : filteredPayables.length === 0 ? (
          <Alert severity="info">
            No hay cuentas por pagar registradas. Los comprobantes con proveedores aparecerán aquí.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Proveedor</TableCell>
                  <TableCell>NIT</TableCell>
                  <TableCell>Documento</TableCell>
                  <TableCell>Descripción</TableCell>
                  <TableCell>F. Emisión</TableCell>
                  <TableCell>F. Vencimiento</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell align="right">Abonado</TableCell>
                  <TableCell align="right">Saldo</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPayables.map((payable) => (
                  <TableRow key={payable.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {payable.supplier_name}
                      </Typography>
                    </TableCell>
                    <TableCell>{payable.supplier_id_number}</TableCell>
                    <TableCell>
                      <Typography fontFamily="monospace" fontWeight="bold">
                        {payable.document_number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {payable.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {new Date(payable.issue_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {new Date(payable.due_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      ${payable.total_amount.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      ${payable.paid_amount.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      <strong>${payable.balance.toLocaleString()}</strong>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={payable.status}
                        size="small"
                        color={payable.status === 'VENCIDA' ? 'error' : 'success'}
                      />
                      {payable.days_overdue > 0 && (
                        <Typography variant="caption" display="block" color="error">
                          {payable.days_overdue} días vencida
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" color="primary" title="Ver detalle">
                        <ViewIcon />
                      </IconButton>
                      <IconButton size="small" color="success" title="Registrar pago">
                        <PaymentIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
};

export default AccountsPayable;
