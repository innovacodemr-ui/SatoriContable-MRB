import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Grid,
  Autocomplete,
  Typography
} from '@mui/material';
import { Save as SaveIcon } from '@mui/icons-material';
import treasuryService, { BankAccount } from '../../../services/treasuryService';
import { accountsService } from '../../../services/api';

interface BankAccountFormProps {
  initialData?: BankAccount;
  onSave: () => void;
  onCancel: () => void;
}

const BankAccountForm: React.FC<BankAccountFormProps> = ({ initialData, onSave, onCancel }) => {
  const [formData, setFormData] = useState<BankAccount>({
    name: '',
    account_number: '',
    bank_name: '',
    currency: 'COP',
    gl_account: 0
  });

  const [accounts, setAccounts] = useState<any[]>([]);
  const [selectedGlAccount, setSelectedGlAccount] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadAccounts();
    if (initialData) {
      setFormData(initialData);
    }
  }, [initialData]);

  const loadAccounts = async () => {
    try {
      // Fetch accounts (ideally filter for assets/banks if possible, or just all)
      const data = await accountsService.getAll(); 
      const list = Array.isArray(data) ? data : data.results;
      setAccounts(list);

      if (initialData && initialData.gl_account) {
        const found = list.find((acc: any) => acc.id === initialData.gl_account);
        if (found) setSelectedGlAccount(found);
      }
    } catch (error) {
      console.error("Error loading accounts", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGlAccount) {
      alert("Debe seleccionar una cuenta contable.");
      return;
    }

    try {
      setLoading(true);
      const payload = { ...formData, gl_account: selectedGlAccount.id };
      
      if (initialData?.id) {
        await treasuryService.updateBankAccount(initialData.id, payload);
      } else {
        await treasuryService.createBankAccount(payload);
      }
      onSave();
    } catch (error) {
      console.error("Error saving bank account", error);
      alert("Error al guardar la cuenta bancaria.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Box sx={{ mt: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              label="Nombre para mostrar"
              fullWidth
              required
              helperText="Ej: Bancolombia Ahorros"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              label="Número de Cuenta"
              fullWidth
              required
              value={formData.account_number}
              onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              label="Nombre del Banco"
              fullWidth
              required
              helperText="Ej: Bancolombia, Davivienda"
              value={formData.bank_name}
              onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
            />
          </Grid>
          <Grid item xs={12}>
            <Autocomplete
              options={accounts}
              getOptionLabel={(option) => `${option.code} - ${option.name}`}
              value={selectedGlAccount}
              onChange={(_, value) => setSelectedGlAccount(value)}
              renderInput={(params) => (
                <TextField 
                    {...params} 
                    label="Cuenta Contable (PUC)" 
                    required 
                    helperText="Cuenta del Activo a debitar/acreditar"
                />
              )}
            />
          </Grid>
          <Grid item xs={12}>
             <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
                <Button onClick={onCancel}>Cancelar</Button>
                <Button 
                    type="submit" 
                    variant="contained" 
                    disabled={loading}
                    startIcon={<SaveIcon />}
                >
                    Guardar
                </Button>
             </Box>
          </Grid>
        </Grid>
      </Box>
    </form>
  );
};

export default BankAccountForm;
