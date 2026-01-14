import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Button,
} from '@mui/material';
import {
  TrendingUp,
  AccountBalance,
  Receipt,
  People,
  AttachMoney
} from '@mui/icons-material';
import { isDesktop } from '../services/api';
import { reportsService, DashboardMetrics } from '../services/reportsService';
import { toast } from 'react-toastify';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics>({
      period: '...',
      sales_month: 0,
      expenses_month: 0,
      available_cash: 0,
      chart_data: []
  });

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await reportsService.getDashboardMetrics();
      setMetrics(data);
    } catch (error) {
      console.error("Error loading metrics", error);
    }
  }

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(val);
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Tablero de Control
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Periodo: {metrics.period}
        </Typography>
      </Box>

      {/* KPIs */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Ventas del Mes</Typography>
                  <Typography variant="h4" fontWeight="bold" sx={{ color: '#4caf50' }}>
                    {formatCurrency(metrics.sales_month)}
                  </Typography>
                </Box>
                <TrendingUp style={{ fontSize: 40, color: '#4caf50' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Gastos del Mes</Typography>
                  <Typography variant="h4" fontWeight="bold" sx={{ color: '#f44336' }}>
                    {formatCurrency(metrics.expenses_month)}
                  </Typography>
                </Box>
                <AccountBalance style={{ fontSize: 40, color: '#f44336' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={4}>
          <Card elevation={2}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Disponible en Bancos</Typography>
                  <Typography variant="h4" fontWeight="bold" sx={{ color: '#2196f3' }}>
                    {formatCurrency(metrics.available_cash)}
                  </Typography>
                </Box>
                <AttachMoney style={{ fontSize: 40, color: '#2196f3' }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Gráfica */}
      <Paper elevation={2} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Resumen Financiero
        </Typography>
        <Box height={400}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={metrics.chart_data}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(val) => `$${val / 1000}k`} />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Bar dataKey="value" name="Monto" barSize={80}>
                 {
                    metrics.chart_data.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill || '#8884d8'} />
                    ))
                  }
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Box>
      </Paper>
    </Box>
  );
};

export default Dashboard;
