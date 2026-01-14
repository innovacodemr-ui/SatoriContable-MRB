import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Button, IconButton, Grid, Card, CardContent,
  CircularProgress, Alert, Tabs, Tab
} from '@mui/material';
import {
  Refresh as RefreshIcon, Visibility as ViewIcon, Payment as PaymentIcon,
  AttachMoney as MoneyIcon
} from '@mui/icons-material';
import { isDesktop } from '../../services/api';
import { toast } from 'react-toastify';

interface AccountReceivable {
  id: number;
  customer_id: number;
  customer_name: string;
  customer_id_number: string;
  document_number: string;
  issue_date: string;
  due_date: string;
  total_amount: number;
  paid_amount: number;
  balance: number;
  status: string;
  days_overdue: number;
}

const AccountsReceivable: React.FC = () => {
  const [receivables, setReceivables] = useState<AccountReceivable[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    loadReceivables();
  }, []);

  const loadReceivables = async () => {
    setLoading(true);
    try {
      if (isDesktop()) {
        // Consulta SQL para obtener cuentas por cobrar desde facturas
        const result = await window.electronAPI!.dbQuery(`
          SELECT 
            ed.id,
            ed.customer_id,
            tp.name as customer_name,
            tp.id_number as customer_id_number,
            ed.prefix || '-' || ed.number as document_number,
            ed.issue_date,
            date(ed.issue_date, '+30 days') as due_date,
            ed.total as total_amount,
            0 as paid_amount,
            ed.total as balance,
            CASE 
              WHEN julianday('now') - julianday(ed.issue_date) > 30 THEN 'VENCIDA'
              ELSE 'VIGENTE'
            END as status,
            CAST(MAX(0, julianday('now') - julianday(ed.issue_date, '+30 days')) AS INTEGER) as days_overdue
          FROM electronic_documents ed
          INNER JOIN third_parties tp ON ed.customer_id = tp.id
          WHERE ed.document_type = 'INVOICE' 
            AND ed.status = 'SENT'
            AND ed.payment_method = 'CREDITO'
          ORDER BY ed.issue_date DESC
        `);
        
        if (result.success) {
          setReceivables(result.data || []);
        }
      } else {
        // Llamada API para web
        toast.info('Función disponible próximamente en versión web');
      }
    } catch (error: any) {
      toast.error('Error al cargar cuentas por cobrar');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotals = () => {
    const total = receivables.reduce((sum, r) => sum + r.total_amount, 0);
    const paid = receivables.reduce((sum, r) => sum + r.paid_amount, 0);
    const balance = receivables.reduce((sum, r) => sum + r.balance, 0);
    const overdue = receivables.filter(r => r.status === 'VENCIDA').reduce((sum, r) => sum + r.balance, 0);
    
    return { total, paid, balance, overdue };
  };

  const filteredReceivables = receivables.filter(r => {
    if (tabValue === 0) return true; // Todas
    if (tabValue === 1) return r.status === 'VIGENTE'; // Vigentes
    if (tabValue === 2) return r.status === 'VENCIDA'; // Vencidas
    return true;
  });

  const totals = calculateTotals();

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Cuentas por Cobrar
        </Typography>
        <Box>
          {isDesktop() && (
            <Chip label="Modo Desktop" color="primary" size="small" sx={{ mr: 2 }} />
          )}
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadReceivables}>
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
                Total Facturado
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
                Total Recaudado
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
                Cartera Vencida
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
          <Tab label={`Todas (${receivables.length})`} />
          <Tab label={`Vigentes (${receivables.filter(r => r.status === 'VIGENTE').length})`} />
          <Tab label={`Vencidas (${receivables.filter(r => r.status === 'VENCIDA').length})`} />
        </Tabs>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : filteredReceivables.length === 0 ? (
          <Alert severity="info">
            No hay cuentas por cobrar registradas. Las facturas a crédito aparecerán aquí.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Cliente</TableCell>
                  <TableCell>NIT/CC</TableCell>
                  <TableCell>Documento</TableCell>
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
                {filteredReceivables.map((receivable) => (
                  <TableRow key={receivable.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {receivable.customer_name}
                      </Typography>
                    </TableCell>
                    <TableCell>{receivable.customer_id_number}</TableCell>
                    <TableCell>
                      <Typography fontFamily="monospace" fontWeight="bold">
                        {receivable.document_number}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {new Date(receivable.issue_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {new Date(receivable.due_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      ${receivable.total_amount.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      ${receivable.paid_amount.toLocaleString()}
                    </TableCell>
                    <TableCell align="right">
                      <strong>${receivable.balance.toLocaleString()}</strong>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={receivable.status}
                        size="small"
                        color={receivable.status === 'VENCIDA' ? 'error' : 'success'}
                      />
                      {receivable.days_overdue > 0 && (
                        <Typography variant="caption" display="block" color="error">
                          {receivable.days_overdue} días vencida
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

export default AccountsReceivable;
