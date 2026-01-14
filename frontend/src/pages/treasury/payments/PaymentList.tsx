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
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import { Add as AddIcon, Visibility as VisibilityIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import treasuryService, { PaymentOut } from '../../../services/treasuryService';

const PaymentList: React.FC = () => {
  const navigate = useNavigate();
  const [payments, setPayments] = useState<PaymentOut[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPayments();
  }, []);

  const loadPayments = async () => {
    try {
      setLoading(true);
      const data = await treasuryService.getPayments();
      setPayments(Array.isArray(data) ? data : data.results);
    } catch (error) {
      console.error("Error loading payments", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Comprobantes de Egreso</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/treasury/payments/new')}
        >
          Nuevo Pago
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Fecha</TableCell>
              <TableCell>Consecutivo</TableCell>
              <TableCell>Tercero</TableCell>
              <TableCell>Banco</TableCell>
              <TableCell align="right">Total Pagado</TableCell>
              <TableCell align="center">Estado</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments.map((payment) => (
              <TableRow key={payment.id}>
                <TableCell>{payment.payment_date}</TableCell>
                <TableCell>CE-{payment.consecutive}</TableCell>
                <TableCell>{payment.third_party}</TableCell>
                <TableCell>{payment.bank_account_name}</TableCell>
                <TableCell align="right">
                  {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(payment.total_amount))}
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={payment.status === 'POSTED' ? 'Contabilizado' : 'Borrador'}
                    color={payment.status === 'POSTED' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Ver Detalle">
                    <IconButton size="small" onClick={() => navigate(`/treasury/payments/${payment.id}`)}>
                      <VisibilityIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {payments.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={7} align="center">No hay comprobantes registrados.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default PaymentList;
