import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow,
  CircularProgress, Chip, Alert, IconButton,
  Dialog, DialogTitle, DialogContent, DialogActions,
  FormControl, InputLabel, Select, MenuItem,
  Tooltip
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  CheckCircle as CheckCircleIcon,
  HourglassEmpty as PendingIcon,
  Error as ErrorIcon,
  Sync as SyncIcon,
  AccountBalance as AccountBalanceIcon,
  Book as BookIcon
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import { receivingService } from '../../services/receivingService';
import { accountingTemplatesService } from '../../services/api';

// Interfaces based on Backend Models
interface InvoiceEvent {
    id: number;
    event_code: string;
    dian_status: 'PENDING' | 'SENT' | 'ACCEPTED' | 'REJECTED';
    cude?: string;
    created_at: string;
}

interface ReceivedInvoice {
    id: number;
    invoice_number: string;
    issuer_name: string;
    issuer_nit: string;
    issue_date: string;
    total_amount: string; // Decimal comes as string usually
    cufe: string;
    events: InvoiceEvent[];
}

interface Template {
    id: number;
    name: string;
}

export const InvoiceInbox: React.FC = () => {
    const [invoices, setInvoices] = useState<ReceivedInvoice[]>([]);
    const [loading, setLoading] = useState(true);
    // State for individual loading: Key=InvoiceID, Value=Boolean
    const [processingEvents, setProcessingEvents] = useState<{ [key: number]: boolean }>({});

    // Accounting State
    const [templates, setTemplates] = useState<Template[]>([]);
    const [openAccountingDialog, setOpenAccountingDialog] = useState(false);
    const [selectedInvoice, setSelectedInvoice] = useState<number | null>(null);
    const [selectedTemplate, setSelectedTemplate] = useState<string>('');    
    const [postingLoading, setPostingLoading] = useState(false);

    useEffect(() => {
        loadInvoices();
        loadTemplates(); // Cargar plantillas al inicio
    }, []);

    const loadInvoices = async () => {
        try {
            setLoading(true);
            const data = await receivingService.listInvoices();
            setInvoices(data);
        } catch (error) {
            console.error("Error loading invoices", error);
            toast.error("Error cargando facturas recibidas");
        } finally {
            setLoading(false);
        }
    };

    const loadTemplates = async () => {
        try {
            const data = await accountingTemplatesService.getAll();
            setTemplates(data.filter((t: any) => t.active)); // Filtrar activas
        } catch (error) {
            console.error("Error loading templates", error);
        }
    };

    const handleSync = async () => {
        try {
            setLoading(true);
            toast.info("Conectando al correo de recepción...");
            const result = await receivingService.syncEmail();
            if (result.logs) {
                result.logs.forEach((log: string) => {
                    if (log.includes('✅')) toast.success(log);
                    else if (log.includes('❌')) toast.error(log);
                    else toast.info(log);
                });
            }
            loadInvoices(); // Reload list
        } catch (error) {
            toast.error("Error al sincronizar correo. Verifica credenciales en el servidor.");
        } finally {
            setLoading(false);
        }
    };

    const handleSendEvent = async (invoiceId: number, eventCode: string) => {
        // 1. Set loading for specific row
        setProcessingEvents(prev => ({ ...prev, [invoiceId]: true }));

        try {
            // 2. Call API
            const response = await receivingService.sendEvent(invoiceId, eventCode);
            
            if (response.status === 'success') {
                toast.success(response.message || "Evento enviado correctamente");
                
                // 3. Optimistic / Reactive Update
                // Replace the invoice in the list with the updated one from server
                if (response.invoice) {
                    setInvoices(prevInvoices => 
                        prevInvoices.map(inv => inv.id === invoiceId ? response.invoice : inv)
                    );
                } else {
                    // Fallback if server doesn't return invoice: reload or patch manually
                    // For now, based on my backend update, it returns 'invoice'
                    loadInvoices(); 
                }
            } else {
                toast.error(response.error || "Error desconocido del servidor");
            }

        } catch (error: any) {
            console.error("Error sending event", error);
            const msg = error.response?.data?.error || error.message || "Error de conexión";
            toast.error(`Falló el envío: ${msg}`);
        } finally {
            // 4. Clear loading
            setProcessingEvents(prev => {
                const newState = { ...prev };
                delete newState[invoiceId];
                return newState;
            });
        }
    };
    
    // --- Accounting Logic ---

    const openPostDialog = (invoiceId: number) => {
        setSelectedInvoice(invoiceId);
        setSelectedTemplate('');
        setOpenAccountingDialog(true);
    };

    const handlePostToAccounting = async () => {
        if (!selectedInvoice || !selectedTemplate) return;

        try {
            setPostingLoading(true);
            const response = await receivingService.postToAccounting(selectedInvoice, parseInt(selectedTemplate));
            toast.success(response.message || "Factura contabilizada exitosamente");
            setOpenAccountingDialog(false);
            // Opcional: Marcar factura como contabilizada visualmente o recargar
        } catch (error: any) {
            console.error(error);
            const msg = error.response?.data?.error || "Error al contabilizar";
            toast.error(msg);
        } finally {
            setPostingLoading(false);
        }
    };


    // Helper to check if event exists and is accepted
    const getEventStatus = (invoice: ReceivedInvoice, code: string) => {
        const event = invoice.events.find(e => e.event_code === code && e.dian_status === 'ACCEPTED');
        return !!event;
    };

    const hasAnyPendingOrRejected = (invoice: ReceivedInvoice, code: string) => {
         // Optional: Check if we tried and failed, to show retry button
         const event = invoice.events.find(e => e.event_code === code);
         return event ? event.dian_status : null;
    };

    return (
        <Box className="p-6">
            <Box className="flex justify-between items-center mb-6">
                <Box>
                    <Typography variant="h4" className="font-bold text-gray-800">
                        Buzón de Recepción (RADIAN)
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                        Gestiona los acuses de recibo de tus compras electrónicas
                    </Typography>
                </Box>
                <Box className="flex gap-2">
                    <Button 
                        variant="contained" 
                        color="secondary" // Color llamativo
                        startIcon={<SyncIcon />}
                        onClick={handleSync}
                        disabled={loading}
                        sx={{ mr: 2 }}
                    >
                        Sincronizar Correo
                    </Button>
                    <Button 
                        variant="outlined" 
                        color="primary" 
                        startIcon={<UploadIcon />}
                        component="label"
                    >
                        Subir XML Manual
                        <input 
                            type="file" 
                            hidden 
                            accept=".xml,.zip" 
                            onChange={async (e) => {
                                if (e.target.files && e.target.files[0]) {
                                    try {
                                        await receivingService.uploadInvoice(e.target.files[0]);
                                        toast.success("Factura subida exitosamente");
                                        loadInvoices();
                                    } catch (err) {
                                        toast.error("Error subiendo archivo");
                                    }
                                }
                            }}
                        />
                    </Button>
                </Box>
            </Box>

            <TableContainer component={Paper} elevation={2} className="rounded-lg overflow-hidden">
                <Table>
                    <TableHead className="bg-gray-100">
                        <TableRow>
                            <TableCell className="font-bold">Fecha</TableCell>
                            <TableCell className="font-bold">Emisor (Proveedor)</TableCell>
                            <TableCell className="font-bold">Factura #</TableCell>
                            <TableCell className="font-bold">Total</TableCell>
                            <TableCell className="font-bold text-center">Eventos RADIAN</TableCell>
                            <TableCell className="font-bold text-center">Contabilidad</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {loading ? (
                            <TableRow>
                                <TableCell colSpan={6} align="center" className="py-8">
                                    <CircularProgress />
                                </TableCell>
                            </TableRow>
                        ) : invoices.length === 0 ? (
                            <TableRow>
                                <TableCell colSpan={6} align="center" className="py-8 text-gray-500">
                                    No hay facturas recibidas. Sube un XML para comenzar.
                                </TableCell>
                            </TableRow>
                        ) : (
                            invoices.map((invoice) => {
                                const isProcessing = processingEvents[invoice.id];
                                const hasAcuse = getEventStatus(invoice, '030');
                                const hasRecibo = getEventStatus(invoice, '032');
                                const hasAceptacion = getEventStatus(invoice, '033');

                                return (
                                    <TableRow key={invoice.id} hover>
                                        <TableCell>{invoice.issue_date}</TableCell>
                                        <TableCell>
                                            <Typography variant="subtitle2">{invoice.issuer_name}</Typography>
                                            <Typography variant="caption" className="text-gray-500">{invoice.issuer_nit}</Typography>
                                        </TableCell>
                                        <TableCell>{invoice.invoice_number}</TableCell>
                                        <TableCell>
                                            ${parseFloat(invoice.total_amount).toLocaleString('es-CO')}
                                        </TableCell>
                                        <TableCell align="center">
                                            <Box className="flex justify-center gap-2 items-center">
                                                
                                                {/* 1. ACUSE DE RECIBO (030) */}
                                                {hasAcuse ? (
                                                    <Chip 
                                                        icon={<CheckCircleIcon />} 
                                                        label="✅ Acuse" 
                                                        color="success" 
                                                        variant="outlined"
                                                        size="small"
                                                        className="font-bold bg-green-50"
                                                    />
                                                ) : (
                                                    <Button
                                                        variant="contained"
                                                        color="primary" // Indigo/Blue
                                                        size="small"
                                                        disabled={isProcessing}
                                                        onClick={() => handleSendEvent(invoice.id, '030')}
                                                        className="bg-indigo-600 hover:bg-indigo-700"
                                                    >
                                                        {isProcessing ? <CircularProgress size={20} color="inherit" /> : "Acuse"}
                                                    </Button>
                                                )}

                                                {/* Arrow Connector */}
                                                <div className={`w-2 h-0.5 ${hasAcuse ? 'bg-indigo-400' : 'bg-gray-300'}`}></div>

                                                {/* 2. RECIBO DEL BIEN (032) */}
                                                {hasRecibo ? (
                                                    <Chip 
                                                        icon={<CheckCircleIcon />}
                                                        label="✅ Bienes" 
                                                        color="success" 
                                                                                                                variant="outlined"
                                                        size="small"
                                                        className="font-bold bg-green-50"
                                                    />
                                                ) : (
                                                    <Button
                                                        variant={hasAcuse ? "contained" : "outlined"}
                                                        color={hasAcuse ? "primary" : "inherit"}
                                                        size="small"
                                                        // Habilitado solo si tiene Acuse (030)
                                                        disabled={!hasAcuse || isProcessing}
                                                        onClick={() => hasAcuse && handleSendEvent(invoice.id, '032')}
                                                        className={hasAcuse ? "bg-blue-600 hover:bg-blue-700" : "text-gray-400 border-gray-300"}
                                                        title={!hasAcuse ? "Requiere Acuse de Recibo primero" : "Confirmar recepción del bien"}
                                                    >
                                                        {isProcessing && hasAcuse && !hasRecibo ? <CircularProgress size={20} color="inherit" /> : "Recibo"}
                                                    </Button>
                                                )}

                                                  {/* Arrow Connector */}
                                                  <div className={`w-2 h-0.5 ${hasRecibo ? 'bg-indigo-400' : 'bg-gray-300'}`}></div>

                                                {/* 3. ACEPTACIÓN (033) */}
                                                {hasAceptacion ? (
                                                    <Chip 
                                                        icon={<CheckCircleIcon />}
                                                        label="✅ Aceptada" 
                                                        color="success" 
                                                        variant="outlined"
                                                        size="small"
                                                        className="font-bold bg-green-50"
                                                    />
                                                ) : (
                                                    <Button
                                                        variant={hasRecibo ? "contained" : "outlined"}
                                                        color={hasRecibo ? "secondary" : "inherit"}
                                                        size="small"
                                                        disabled={!hasRecibo || isProcessing}
                                                        onClick={() => hasRecibo && handleSendEvent(invoice.id, '033')}
                                                        className={hasRecibo ? "bg-purple-600 hover:bg-purple-700" : "text-gray-400 border-gray-300"}
                                                        title={!hasRecibo ? "Requiere Recibo del Bien primero" : "Aceptación Expresa de la Factura"}
                                                    >
                                                         {isProcessing && hasRecibo && !hasAceptacion ? <CircularProgress size={20} color="inherit" /> : "Aceptar"}
                                                    </Button>
                                                )}
                                            </Box>
                                        </TableCell>
                                        <TableCell align="center">
                                            <Tooltip title="Generar Asiento Contable Automático">
                                                <Button
                                                    variant="outlined"
                                                    color="primary"
                                                    size="small"
                                                    startIcon={<BookIcon />}
                                                    onClick={() => openPostDialog(invoice.id)}
                                                >
                                                    Contabilizar
                                                </Button>
                                            </Tooltip>
                                        </TableCell>
                                    </TableRow>
                                );
                            })
                        )}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Dialogo de Contabilización */}
            <Dialog open={openAccountingDialog} onClose={() => setOpenAccountingDialog(false)}>
                <DialogTitle>Contabilizar Factura Recibida</DialogTitle>
                <DialogContent sx={{ minWidth: 400, mt: 1 }}>
                    <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                        Selecciona la plantilla contable que Satori debe aplicar para esta factura.
                    </Typography>
                    <FormControl fullWidth>
                        <InputLabel>Plantilla Contable</InputLabel>
                        <Select
                            value={selectedTemplate}
                            label="Plantilla Contable"
                            onChange={(e) => setSelectedTemplate(e.target.value)}
                        >
                            {templates.map(t => (
                                <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
                            ))}
                        </Select>
                    </FormControl>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenAccountingDialog(false)}>Cancelar</Button>
                    <Button 
                        onClick={handlePostToAccounting} 
                        color="primary" 
                        variant="contained"
                        disabled={postingLoading}
                        startIcon={postingLoading ? <CircularProgress size={20} color="inherit" /> : <AccountBalanceIcon />}
                    >
                        Contabilizar
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default InvoiceInbox;
