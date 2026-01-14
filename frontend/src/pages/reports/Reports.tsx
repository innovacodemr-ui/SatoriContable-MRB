import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

const Reports: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom fontWeight="bold">
        Reportes Contables
      </Typography>
      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography>
          Balance General, Estado de Resultados, y otros reportes
        </Typography>
      </Paper>
    </Box>
  );
};

export default Reports;
