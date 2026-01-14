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
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import treasuryService, { BankAccount } from '../../../services/treasuryService';
import BankAccountForm from './BankAccountForm';

const BankAccountList: React.FC = () => {
  const [banks, setBanks] = useState<BankAccount[]>([]);
  const [loading, setLoading] = useState(true);
  const [openModal, setOpenModal] = useState(false);
  const [selectedBank, setSelectedBank] = useState<BankAccount | undefined>(undefined);

  useEffect(() => {
    loadBanks();
  }, []);

  const loadBanks = async () => {
    try {
      setLoading(true);
      const data = await treasuryService.getBankAccounts();
      setBanks(Array.isArray(data) ? data : data.results);
    } catch (error) {
      console.error("Error loading banks", error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenModal = (bank?: BankAccount) => {
    setSelectedBank(bank);
    setOpenModal(true);
  };

  const handleCloseModal = () => {
    setSelectedBank(undefined);
    setOpenModal(false);
    loadBanks();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Cuentas Bancarias</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => handleOpenModal()}
        >
          Nuevo Banco
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Número de Cuenta</TableCell>
              <TableCell>Banco</TableCell>
              <TableCell>Moneda</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {banks.map((bank) => (
              <TableRow key={bank.id}>
                <TableCell>{bank.name}</TableCell>
                <TableCell>{bank.account_number}</TableCell>
                <TableCell>{bank.bank_name}</TableCell>
                <TableCell>{bank.currency}</TableCell>
                <TableCell align="right">
                  <IconButton onClick={() => handleOpenModal(bank)} color="primary">
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {banks.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={5} align="center">No hay cuentas bancarias registradas.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openModal} onClose={() => setOpenModal(false)} fullWidth maxWidth="sm">
        <DialogTitle>{selectedBank ? 'Editar Banco' : 'Nueva Cuenta Bancaria'}</DialogTitle>
        <DialogContent>
          <BankAccountForm 
            initialData={selectedBank} 
            onSave={handleCloseModal} 
            onCancel={() => setOpenModal(false)} 
          />
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default BankAccountList;
