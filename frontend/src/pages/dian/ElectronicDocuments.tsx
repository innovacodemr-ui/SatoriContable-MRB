import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, TextField, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, IconButton,
  Chip, Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem, Grid, Alert,
  CircularProgress, Divider, Autocomplete
} from '@mui/material';
import {
  Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon,
  Refresh as RefreshIcon, Send as SendIcon, Visibility as ViewIcon,
  Print as PrintIcon
} from '@mui/icons-material';
import { electronicDocumentsService, thirdPartiesService, isDesktop } from '../../services/api';
import { toast } from 'react-toastify';

interface ElectronicDocument {
  id?: number;
  document_type: string;
  prefix: string;
  number: string;
  issue_date: string;
  customer_id: number;
  customer_name?: string;
  payment_method: string;
  payment_means: string;
  subtotal: number;
  tax_total: number;
  total: number;
  status: string;
  cufe?: string;
  dian_response?: string;
  lines?: ElectronicDocumentLine[];
  taxes?: ElectronicDocumentTax[];
}

interface ElectronicDocumentLine {
  line_number: number;
  product_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount: number;
  line_total: number;
}

interface ElectronicDocumentTax {
  tax_category: string;
  tax_rate: number;
  taxable_amount: number;
  tax_amount: number;
}

const ElectronicDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<ElectronicDocument[]>([]);
  const [thirdParties, setThirdParties] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<ElectronicDocument | null>(null);
  const [formData, setFormData] = useState<Partial<ElectronicDocument>>({
    document_type: 'INVOICE',
    prefix: 'SEFE',
    number: '',
    issue_date: new Date().toISOString().split('T')[0],
    payment_method: 'CONTADO',
    payment_means: 'EFECTIVO',
    lines: [],
    taxes: []
  });
  const [currentLine, setCurrentLine] = useState<Partial<ElectronicDocumentLine>>({
    line_number: 1,
    product_code: '',
    description: '',
    quantity: 1,
    unit_price: 0,
    discount: 0,
    line_total: 0
  });

  useEffect(() => {
    loadDocuments();
    loadThirdParties();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await electronicDocumentsService.getAll();
      setDocuments(Array.isArray(data) ? data : []);
    } catch (error: any) {
      toast.error('Error al cargar documentos');
      setDocuments([]);
    } finally {
      setLoading(false);
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
      document_type: 'INVOICE',
      prefix: 'SEFE',
      number: String(Date.now()).slice(-8),
      issue_date: new Date().toISOString().split('T')[0],
      payment_method: 'CONTADO',
      payment_means: 'EFECTIVO',
      customer_id: 0,
      lines: [],
      taxes: []
    });
    setCurrentLine({
      line_number: 1,
      product_code: '',
      description: '',
      quantity: 1,
      unit_price: 0,
      discount: 0,
      line_total: 0
    });
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const calculateLineTotal = (quantity: number, unitPrice: number, discount: number) => {
    return quantity * unitPrice - discount;
  };

  const handleAddLine = () => {
    if (!currentLine.product_code || !currentLine.description || currentLine.quantity === 0) {
      toast.error('Complete los campos de la línea');
      return;
    }

    const lineTotal = calculateLineTotal(
      currentLine.quantity || 0,
      currentLine.unit_price || 0,
      currentLine.discount || 0
    );

    const newLine = {
      ...currentLine,
      line_number: (formData.lines?.length || 0) + 1,
      line_total: lineTotal
    } as ElectronicDocumentLine;

    const newLines = [...(formData.lines || []), newLine];
    setFormData({ ...formData, lines: newLines });

    // Calcular impuestos automáticamente (IVA 19%)
    const taxableAmount = lineTotal;
    const taxAmount = taxableAmount * 0.19;
    const existingTax = formData.taxes?.find(t => t.tax_category === 'IVA');

    let newTaxes = formData.taxes || [];
    if (existingTax) {
      newTaxes = newTaxes.map(t =>
        t.tax_category === 'IVA'
          ? {
              ...t,
              taxable_amount: t.taxable_amount + taxableAmount,
              tax_amount: t.tax_amount + taxAmount
            }
          : t
      );
    } else {
      newTaxes.push({
        tax_category: 'IVA',
        tax_rate: 19,
        taxable_amount: taxableAmount,
        tax_amount: taxAmount
      });
    }

    setFormData({ ...formData, lines: newLines, taxes: newTaxes });

    // Reset current line
    setCurrentLine({
      line_number: newLines.length + 1,
      product_code: '',
      description: '',
      quantity: 1,
      unit_price: 0,
      discount: 0,
      line_total: 0
    });
  };

  const handleRemoveLine = (index: number) => {
    const removedLine = formData.lines![index];
    const newLines = formData.lines?.filter((_, i) => i !== index);

    // Actualizar impuestos
    const taxAmount = removedLine.line_total * 0.19;
    const newTaxes = formData.taxes?.map(t =>
      t.tax_category === 'IVA'
        ? {
            ...t,
            taxable_amount: t.taxable_amount - removedLine.line_total,
            tax_amount: t.tax_amount - taxAmount
          }
        : t
    ).filter(t => t.taxable_amount > 0);

    setFormData({ ...formData, lines: newLines, taxes: newTaxes });
  };

  const calculateTotals = () => {
    const subtotal = formData.lines?.reduce((sum, line) => sum + line.line_total, 0) || 0;
    const taxTotal = formData.taxes?.reduce((sum, tax) => sum + tax.tax_amount, 0) || 0;
    const total = subtotal + taxTotal;
    return { subtotal, taxTotal, total };
  };

  const handleSubmit = async () => {
    if (!formData.customer_id) {
      toast.error('Debe seleccionar un cliente');
      return;
    }

    if ((formData.lines?.length || 0) === 0) {
      toast.error('Debe agregar al menos una línea al documento');
      return;
    }

    const { subtotal, taxTotal, total } = calculateTotals();

    try {
      const documentData = {
        ...formData,
        subtotal,
        tax_total: taxTotal,
        total,
        status: 'DRAFT'
      };

      await electronicDocumentsService.create(documentData as ElectronicDocument);
      toast.success('Documento creado correctamente');
      handleCloseDialog();
      loadDocuments();
    } catch (error: any) {
      toast.error('Error: ' + (error.message || 'Error desconocido'));
    }
  };

  const handleSend = async (id: number) => {
    if (window.confirm('¿Está seguro de enviar este documento a la DIAN?')) {
      try {
        await electronicDocumentsService.send(id);
        toast.success('Documento enviado a la DIAN correctamente');
        loadDocuments();
      } catch (error: any) {
        toast.error('Error al enviar: ' + (error.message || 'Error desconocido'));
      }
    }
  };

  const handleView = async (doc: ElectronicDocument) => {
    try {
      const fullDoc = await electronicDocumentsService.getById(doc.id!);
      setViewingDocument(fullDoc);
      setOpenViewDialog(true);
    } catch (error: any) {
      toast.error('Error al cargar detalle');
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('¿Está seguro de eliminar este documento?')) {
      try {
        await electronicDocumentsService.delete(id);
        toast.success('Documento eliminado correctamente');
        loadDocuments();
      } catch (error: any) {
        toast.error('Error al eliminar');
      }
    }
  };

  const { subtotal, taxTotal, total } = calculateTotals();

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          Facturación Electrónica DIAN
        </Typography>
        <Box>
          {isDesktop() && (
            <Chip label="Modo Desktop" color="primary" size="small" sx={{ mr: 2 }} />
          )}
          <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenDialog}>
            Nuevo Documento
          </Button>
        </Box>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Box display="flex" gap={2} mb={3}>
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadDocuments}>
            Actualizar
          </Button>
        </Box>

        {loading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Alert severity="info">
            No hay documentos registrados. Haz clic en "Nuevo Documento" para crear uno.
          </Alert>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Número</TableCell>
                  <TableCell>Fecha</TableCell>
                  <TableCell>Cliente</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id} hover>
                    <TableCell>
                      <Chip
                        label={doc.document_type}
                        size="small"
                        color={
                          doc.document_type === 'INVOICE'
                            ? 'primary'
                            : doc.document_type === 'CREDIT_NOTE'
                            ? 'warning'
                            : 'info'
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Typography fontFamily="monospace" fontWeight="bold">
                        {doc.prefix}-{doc.number}
                      </Typography>
                    </TableCell>
                    <TableCell>{new Date(doc.issue_date).toLocaleDateString()}</TableCell>
                    <TableCell>{doc.customer_name || `ID: ${doc.customer_id}`}</TableCell>
                    <TableCell align="right">
                      <strong>${doc.total.toLocaleString()}</strong>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={doc.status}
                        size="small"
                        color={
                          doc.status === 'SENT'
                            ? 'success'
                            : doc.status === 'REJECTED'
                            ? 'error'
                            : 'default'
                        }
                      />
                    </TableCell>
                    <TableCell align="right">
                      <IconButton size="small" onClick={() => handleView(doc)} color="primary">
                        <ViewIcon />
                      </IconButton>
                      {doc.status === 'DRAFT' && (
                        <>
                          <IconButton
                            size="small"
                            onClick={() => handleSend(doc.id!)}
                            color="success"
                          >
                            <SendIcon />
                          </IconButton>
                          <IconButton
                            size="small"
                            onClick={() => handleDelete(doc.id!)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </>
                      )}
                      {doc.status === 'SENT' && (
                        <IconButton size="small" color="default">
                          <PrintIcon />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Dialog Crear Documento */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="lg" fullWidth>
        <DialogTitle>Nuevo Documento Electrónico</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Tipo Documento</InputLabel>
                <Select
                  value={formData.document_type}
                  onChange={(e) => setFormData({ ...formData, document_type: e.target.value })}
                  label="Tipo Documento"
                >
                  <MenuItem value="INVOICE">Factura de Venta</MenuItem>
                  <MenuItem value="CREDIT_NOTE">Nota Crédito</MenuItem>
                  <MenuItem value="DEBIT_NOTE">Nota Débito</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                label="Prefijo"
                value={formData.prefix}
                onChange={(e) => setFormData({ ...formData, prefix: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
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
                label="Fecha Emisión"
                value={formData.issue_date}
                onChange={(e) => setFormData({ ...formData, issue_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
                required
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Autocomplete
                options={thirdParties}
                getOptionLabel={(option) =>
                  `${option.id_number} - ${option.name}${option.trade_name ? ` (${option.trade_name})` : ''}`
                }
                onChange={(_, newValue) => {
                  setFormData({ ...formData, customer_id: newValue?.id || 0 });
                }}
                renderInput={(params) => <TextField {...params} label="Cliente" required />}
              />
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Forma de Pago</InputLabel>
                <Select
                  value={formData.payment_method}
                  onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                  label="Forma de Pago"
                >
                  <MenuItem value="CONTADO">Contado</MenuItem>
                  <MenuItem value="CREDITO">Crédito</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={3}>
              <FormControl fullWidth>
                <InputLabel>Medio de Pago</InputLabel>
                <Select
                  value={formData.payment_means}
                  onChange={(e) => setFormData({ ...formData, payment_means: e.target.value })}
                  label="Medio de Pago"
                >
                  <MenuItem value="EFECTIVO">Efectivo</MenuItem>
                  <MenuItem value="TRANSFERENCIA">Transferencia</MenuItem>
                  <MenuItem value="TARJETA_CREDITO">Tarjeta Crédito</MenuItem>
                  <MenuItem value="TARJETA_DEBITO">Tarjeta Débito</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Líneas del Documento
              </Typography>
            </Grid>

            {/* Agregar Línea */}
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                size="small"
                label="Código"
                value={currentLine.product_code}
                onChange={(e) => setCurrentLine({ ...currentLine, product_code: e.target.value })}
              />
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
            <Grid item xs={12} sm={1}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Cant."
                value={currentLine.quantity || ''}
                onChange={(e) => setCurrentLine({ ...currentLine, quantity: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Precio Unit."
                value={currentLine.unit_price || ''}
                onChange={(e) => setCurrentLine({ ...currentLine, unit_price: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Descuento"
                value={currentLine.discount || ''}
                onChange={(e) => setCurrentLine({ ...currentLine, discount: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} sm={2}>
              <TextField
                fullWidth
                size="small"
                label="Total"
                value={calculateLineTotal(
                  currentLine.quantity || 0,
                  currentLine.unit_price || 0,
                  currentLine.discount || 0
                ).toLocaleString()}
                InputProps={{ readOnly: true }}
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
                      <TableCell>#</TableCell>
                      <TableCell>Código</TableCell>
                      <TableCell>Descripción</TableCell>
                      <TableCell align="right">Cantidad</TableCell>
                      <TableCell align="right">Precio Unit.</TableCell>
                      <TableCell align="right">Descuento</TableCell>
                      <TableCell align="right">Total</TableCell>
                      <TableCell align="center">Acción</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {formData.lines?.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>{line.line_number}</TableCell>
                        <TableCell>{line.product_code}</TableCell>
                        <TableCell>{line.description}</TableCell>
                        <TableCell align="right">{line.quantity}</TableCell>
                        <TableCell align="right">${line.unit_price.toLocaleString()}</TableCell>
                        <TableCell align="right">${line.discount.toLocaleString()}</TableCell>
                        <TableCell align="right">
                          <strong>${line.line_total.toLocaleString()}</strong>
                        </TableCell>
                        <TableCell align="center">
                          <IconButton size="small" onClick={() => handleRemoveLine(index)} color="error">
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            {/* Resumen de Totales */}
            <Grid item xs={12}>
              <Paper variant="outlined" sx={{ p: 2, mt: 2, bgcolor: 'grey.50' }}>
                <Grid container spacing={2}>
                  <Grid item xs={8}>
                    <Typography variant="h6">Impuestos</Typography>
                    {formData.taxes?.map((tax, index) => (
                      <Box key={index} display="flex" justifyContent="space-between">
                        <Typography>
                          {tax.tax_category} ({tax.tax_rate}%)
                        </Typography>
                        <Typography>${tax.tax_amount.toLocaleString()}</Typography>
                      </Box>
                    ))}
                  </Grid>
                  <Grid item xs={4}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography>Subtotal:</Typography>
                      <Typography>${subtotal.toLocaleString()}</Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography>Impuestos:</Typography>
                      <Typography>${taxTotal.toLocaleString()}</Typography>
                    </Box>
                    <Divider sx={{ my: 1 }} />
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="h6">Total:</Typography>
                      <Typography variant="h6" color="primary">
                        ${total.toLocaleString()}
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancelar</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            color="primary"
            disabled={!formData.customer_id || (formData.lines?.length || 0) === 0}
          >
            Guardar Documento
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog Ver Documento */}
      <Dialog open={openViewDialog} onClose={() => setOpenViewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Detalle del Documento Electrónico</DialogTitle>
        <DialogContent>
          {viewingDocument && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Tipo
                  </Typography>
                  <Chip label={viewingDocument.document_type} size="small" />
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Número
                  </Typography>
                  <Typography variant="body1" fontFamily="monospace" fontWeight="bold">
                    {viewingDocument.prefix}-{viewingDocument.number}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Fecha Emisión
                  </Typography>
                  <Typography variant="body1">
                    {new Date(viewingDocument.issue_date).toLocaleDateString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Estado
                  </Typography>
                  <Chip
                    label={viewingDocument.status}
                    size="small"
                    color={viewingDocument.status === 'SENT' ? 'success' : 'default'}
                  />
                </Grid>
                {viewingDocument.cufe && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="text.secondary">
                      CUFE
                    </Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      {viewingDocument.cufe}
                    </Typography>
                  </Grid>
                )}
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="h6" gutterBottom>
                Líneas
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Código</TableCell>
                      <TableCell>Descripción</TableCell>
                      <TableCell align="right">Cantidad</TableCell>
                      <TableCell align="right">Precio</TableCell>
                      <TableCell align="right">Total</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {viewingDocument.lines?.map((line, index) => (
                      <TableRow key={index}>
                        <TableCell>{line.product_code}</TableCell>
                        <TableCell>{line.description}</TableCell>
                        <TableCell align="right">{line.quantity}</TableCell>
                        <TableCell align="right">${(line.unit_price || 0).toLocaleString()}</TableCell>
                        <TableCell align="right">${(line.line_total || 0).toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                    <TableRow>
                      <TableCell colSpan={4} align="right">
                        <strong>Subtotal:</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>${(viewingDocument.subtotal || 0).toLocaleString()}</strong>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={4} align="right">
                        <strong>Impuestos:</strong>
                      </TableCell>
                      <TableCell align="right">
                        <strong>${(viewingDocument.tax_total || 0).toLocaleString()}</strong>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={4} align="right">
                        <Typography variant="h6">TOTAL:</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="h6" color="primary">
                          ${(viewingDocument.total || 0).toLocaleString()}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenViewDialog(false)}>Cerrar</Button>
          {viewingDocument?.status === 'SENT' && (
            <Button variant="contained" startIcon={<PrintIcon />}>
              Imprimir
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ElectronicDocuments;
