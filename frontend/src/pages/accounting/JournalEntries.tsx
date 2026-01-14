import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, TextField, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, IconButton,
  Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Grid, Alert,
  CircularProgress, Divider
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  Refresh as RefreshIcon, Check as CheckIcon, Visibility as ViewIcon
} from '@mui/icons-material';
import { journalEntriesService, accountsService, thirdPartiesService, isDesktop } from '../../services/api';
import { toast } from 'react-toastify';

interface JournalEntry {
  id?: number;
  number: string;
  date: string;
  entry_type: string;
  description: string;
  status: string;
  lines?: JournalEntryLine[];
}

interface JournalEntryLine {
  account_id: number;
  third_party_id?: number;
  cost_center_id?: number;
  description: string;
  debit: number;
  credit: number;
}

const JournalEntries: React.FC = () => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [thirdParties, setThirdParties] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [viewingEntry, setViewingEntry] = useState<JournalEntry | null>(null);
  const [formData, setFormData] = useState<Partial<JournalEntry>>({
    number: '',
    date: new Date().toISOString().split('T')[0],
    entry_type: 'DIARIO',
    description: '',
    lines: []
  });
  const [currentLine, setCurrentLine] = useState<Partial<JournalEntryLine>>({
    account_id: 0,
    description: '',
    debit: 0,
    credit: 0
  });

  useEffect(() => {
    loadEntries();
    loadAccounts();
    loadThirdParties();
  }, []);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const data = await journalEntriesService.getAll();
      setEntries(Array.isArray(data) ? data : []);
    } catch (error: any) {
      toast.error('Error al cargar comprobantes');
      setEntries([]);
    } finally {
      setLoading(false);
    }
  };

  const loadAccounts = async () => {
    try {
      const data = await accountsService.getAll();
      setAccounts(Array.isArray(data) ? data : []);
    } catch (error) {
      setAccounts([]);
    }
  };

  const loadThirdParties = async () => {
    try {
      const data = await thirdPartiesService.getAll();
      setThirdParties(Array.isArray(data) ? data : []);
    } catch (error) {
      setThirdParties([]);
    }
  };

  const handleOpenDialog = () => {
    setFormData({
      number: `CE-${Date.now()}`,
      date: new Date().toISOString().split('T')[0],
      entry_type: 'DIARIO',
      description: '',
      lines: []
    });
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleAddLine = () => {
    if (!currentLine.account_id || (currentLine.debit === 0 && currentLine.credit === 0)) {
      toast.error('Debe seleccionar una cuenta e ingresar débito o crédito');
      return;
    }

    const newLines = [...(formData.lines || []), currentLine as JournalEntryLine];
    setFormData({ ...formData, lines: newLines });
    setCurrentLine({
      account_id: 0,
      description: '',
      debit: 0,
      credit: 0
    });
  };

  const handleRemoveLine = (index: number) => {
    const newLines = formData.lines?.filter((_, i) => i !== index);
    setFormData({ ...formData, lines: newLines });
  };

  const calculateTotals = () => {
    const totalDebit = formData.lines?.reduce((sum, line) => sum + (line.debit || 0), 0) || 0;
    const totalCredit = formData.lines?.reduce((sum, line) => sum + (line.credit || 0), 0) || 0;
    return { totalDebit, totalCredit, isBalanced: totalDebit === totalCredit };
  };

  const handleSubmit = async () => {
    const { totalDebit, totalCredit, isBalanced } = calculateTotals();

    if (!isBalanced) {
      toast.error(`El comprobante no está balanceado. Débito: $${totalDebit.toLocaleString()}, Crédito: $${totalCredit.toLocaleString()}`);
      return;
    }

    if ((formData.lines?.length || 0) === 0) {
      toast.error('Debe agregar al menos una línea al comprobante');
      return;
    }

    try {
      await journalEntriesService.create(formData as JournalEntry);
      toast.success('Comprobante creado correctamente');
      handleCloseDialog();
      loadEntries();
    } catch (error: any) {
      toast.error('Error: ' + (error.message || 'Error desconocido'));
    }
  };

  const handlePost = async (id: number) => {
    if (window.confirm('¿Está seguro de contabilizar este comprobante? No se podrá modificar después.')) {
      try {
        await journalEntriesService.post(id);
        toast.success('Comprobante contabilizado correctamente');
        loadEntries();
      } catch (error: any) {
        toast.error('Error al contabilizar: ' + (error.message || 'Error desconocido'));
      }
    }
  };

  const handleView = async (entry: JournalEntry) => {
    try {
      const fullEntry = await journalEntriesService.getById(entry.id!);
      setViewingEntry(fullEntry);
      setOpenViewDialog(true);
    } catch (error: any) {
      toast.error('Error al cargar detalle');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Está seguro de eliminar este comprobante?')) {
      try {
        await journalEntriesService.delete(id);
        toast.success('Comprobante eliminado correctamente');
        loadEntries();
      } catch (error: any) {
        toast.error('Error al eliminar');
      }
    }
  };

  const getAccountName = (id: number) => {
    const account = accounts.find(a => a.id === id);
    return account ? `${account.code} - ${account.name}` : 'N/A';
  };

  const { totalDebit, totalCredit, isBalanced } = calculateTotals();

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Comprobantes Contables
        </Typography>
        <Box>
          {isDesktop() && (
            <Chip label="Modo Desktop" color="primary" size="small" sx={{ mr: 2 }} />
          )}
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenDialog}>
            Nuevo Comprobante
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Box display="flex" gap={2} mb={3}>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadEntries}>
            Actualizar
          </Button>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : entries.length === 0 ? (
          <Alert severity="info">
            No hay comprobantes registrados. Haz clic en "Nuevo Comprobante" para crear uno.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Número</TableCell>
                  <TableCell>Fecha</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Descripción</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id} hover>
                    <TableCell>
                      <Typography fontFamily="monospace" fontWeight="bold">
                        {entry.number}
                      </Typography>
                    </TableCell>
                    <TableCell>{new Date(entry.date).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <Chip label={entry.entry_type} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>{entry.description}</TableCell>
                    <TableCell>
                      <Chip
                        label={entry.status}
                        size="small"
                        color={
                          entry.status === 'POSTED'
                            ? 'success'
                            : entry.status === 'CANCELLED'
                            ? 'error'
                            : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleView(entry)} color="primary">
                        <ViewIcon />
                      </IconButton>
                      {entry.status === 'DRAFT' && (
                        <>
                          <IconButton
                            size="small"
                            onClick={() => handlePost(entry.id!)}
                            color="success"
                          >
                            <CheckIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(entry.id!)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Dialog Crear Comprobante */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="lg" fullWidth>
        <DialogTitle>Nuevo Comprobante Contable</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Número"
                value={formData.number}
                onChange={(e) => setFormData({ ...formData, number: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="date"
                label="Fecha"
                value={formData.date}
                onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Tipo</InputLabel>
                <Select
                  value={formData.entry_type}
                  onChange={(e) => setFormData({ ...formData, entry_type: e.target.value })}
                  label="Tipo"
                >
                  <MenuItem value="APERTURA">Apertura</MenuItem>
                  <MenuItem value="DIARIO">Diario</MenuItem>
                  <MenuItem value="AJUSTE">Ajuste</MenuItem>
                  <MenuItem value="CIERRE">Cierre</MenuItem>
                  <MenuItem value="NOTA">Nota</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Descripción"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Líneas del Comprobante
              </Typography>
            </Grid>

            {/* Agregar Línea */}
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth size="small">
                <InputLabel>Cuenta</InputLabel>
                <Select
                  value={currentLine.account_id}
                  onChange={(e) => setCurrentLine({ ...currentLine, account_id: Number(e.target.value) })}
                  label="Cuenta"
                >
                  {accounts.map((account) => (
                    <MenuItem key={account.id} value={account.id}>
                      {account.code} - {account.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                size="small"
                label="Descripción"
                value={currentLine.description}
                onChange={(e) => setCurrentLine({ ...currentLine, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Débito"
                value={currentLine.debit || ''}
                onChange={(e) => setCurrentLine({ ...currentLine, debit: Number(e.target.value), credit: 0 })}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Crédito"
                value={currentLine.credit || ''}
                onChange={(e) => setCurrentLine({ ...currentLine, credit: Number(e.target.value), debit: 0 })}
              />
            </Grid>
            <Grid item xs={12} sm={1}>
              <Button fullWidth variant="contained" size="small" onClick={handleAddLine}>
                <AddIcon />
              </Button>
            </Grid>

            {/* Tabla de Líneas */}
            <Grid item xs={12}>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Cuenta</TableCell>
                      <TableCell>Descripción</TableCell>
                      <TableCell align="right">Débito</TableCell>
                      <TableCell align="right">Crédito</TableCell>
                      <TableCell align="center">Acción</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {formData.lines?.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>{getAccountName(line.account_id)}</TableCell>
                        <TableCell>{line.description}</TableCell>
                        <TableCell align="right">
                          ${line.debit.toLocaleString()}
                        </TableCell>
                        <TableCell align="right">
                          ${line.credit.toLocaleString()}
                        </TableCell>
                        <TableCell align="center">
                          <IconButton size="small" onClick={() => handleRemoveLine(index)} color="error">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell colSpan={2} align="right">
                        <strong>TOTALES:</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>${totalDebit.toLocaleString()}</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>${totalCredit.toLocaleString()}</strong>
                      </TableCell>
                      <TableCell align="center">
                        {isBalanced ? (
                          <Chip label="Balanceado" color="success" size="small" />
                        ) : (
                          <Chip label="Desbalanceado" color="error" size="small" />
                        )}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary" disabled={!isBalanced}>
            Guardar Comprobante
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Ver Comprobante */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Detalle del Comprobante</DialogTitle>
        <DialogContent>
          {viewingEntry && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Número
                  </Typography>
                  <Typography variant="body1">{viewingEntry.number}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Fecha
                  </Typography>
                  <Typography variant="body1">
                    {new Date(viewingEntry.date).toLocaleDateString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Tipo
                  </Typography>
                  <Chip label={viewingEntry.entry_type} size="small" />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Estado
                  </Typography>
                  <Chip
                    label={viewingEntry.status}
                    size="small"
                    color={viewingEntry.status === 'POSTED' ? 'success' : 'default'}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Descripción
                  </Typography>
                  <Typography variant="body1">{viewingEntry.description}</Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Movimientos
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Cuenta</TableCell>
                      <TableCell>Descripción</TableCell>
                      <TableCell align="right">Débito</TableCell>
                      <TableCell align="right">Crédito</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {viewingEntry.lines?.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>{getAccountName(line.account_id)}</TableCell>
                        <TableCell>{line.description}</TableCell>
                        <TableCell align="right">${line.debit.toLocaleString()}</TableCell>
                        <TableCell align="right">${line.credit.toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Cerrar</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default JournalEntries;
