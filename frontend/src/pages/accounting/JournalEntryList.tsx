import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Collapse,
  Button,
  CircularProgress
} from '@mui/material';
import {
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowUp as KeyboardArrowUpIcon,
  Link as LinkIcon,
  Visibility as VisibilityIcon
} from '@mui/icons-material';
import { journalEntriesService } from '../../services/api';
import { toast } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

interface JournalEntryLine {
  id: number;
  entry: number;
  line_number: number;
  account_code: string;
  account_name: string;
  description: string;
  debit: number;
  credit: number;
  third_party: number | null; 
  // Podríamos expandir third_party si el backend lo envía full, 
  // pero el serializer actual envía ID o habría que ajustar serializer para enviar nombre. 
  // Asumamos que el backend envía nombre si ajustamos, por ahora ID.
}

interface SourceDocumentInfo {
  type: string;
  app_label: string;
  id: number;
  str_repr: string;
}

interface JournalEntry {
  id: number;
  number: string;
  date: string;
  description: string;
  status: 'DRAFT' | 'POSTED' | 'CANCELLED';
  total_debit: number;
  total_credit: number;
  is_balanced: boolean;
  lines: JournalEntryLine[];
  source_document_info: SourceDocumentInfo | null;
}

const Row = (props: { row: JournalEntry }) => {
  const { row } = props;
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleNavigateSource = () => {
    if (!row.source_document_info) return;
    
    const { app_label, type, id } = row.source_document_info;
    let path = '';

    // Mapeo de rutas según modelo origen
    if (app_label === 'electronic_events' && type === 'receivedinvoice') {
        // Redirigir a inbox Radian
        path = `/dian/inbox`; 
        // Nota: Si existiera vista detalle, sería /radian/inbox/{id}
    } else if (app_label === 'invoicing' && type === 'invoice') {
        path = `/invoices/${id}`;
    } else if (app_label === 'payroll') {
        path = `/payroll/documents`;
    } else {
       toast.info(`Navegación no configurada para ${type}`);
       return;
    }
    
    navigate(path);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(value);
  };

  return (
    <React.Fragment>
      <TableRow sx={{ '& > *': { borderBottom: 'unset' } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {row.date}
        </TableCell>
        <TableCell>{row.number}</TableCell>
        <TableCell>{row.description}</TableCell>
        <TableCell align="right">{formatCurrency(row.total_debit)}</TableCell>
        <TableCell align="right">{formatCurrency(row.total_credit)}</TableCell>
        <TableCell align="center">
           {row.status === 'POSTED' && <Chip label="Contabilizado" color="success" size="small" />}
           {row.status === 'DRAFT' && <Chip label="Borrador" color="warning" size="small" />}
           {row.status === 'CANCELLED' && <Chip label="Anulado" color="error" size="small" />}
        </TableCell>
        <TableCell align="center">
            {row.source_document_info && (
                <Button 
                    size="small" 
                    startIcon={<LinkIcon />} 
                    onClick={handleNavigateSource}
                    variant="outlined"
                    sx={{ textTransform: 'none' }}
                >
                    Ver Soporte
                </Button>
            )}
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={8}>
          <Collapse in={open} timeout="auto" unmountOnExit>
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                Detalle de Movimientos
              </Typography>
              <Table size="small" aria-label="purchases">
                <TableHead>
                  <TableRow>
                    <TableCell>Cuenta</TableCell>
                    <TableCell>Descripción Línea</TableCell>
                    <TableCell align="right">Débito</TableCell>
                    <TableCell align="right">Crédito</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {row.lines && row.lines.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell component="th" scope="row">
                        {line.account_code} - {line.account_name}
                      </TableCell>
                      <TableCell>{line.description}</TableCell>
                      <TableCell align="right">{formatCurrency(line.debit)}</TableCell>
                      <TableCell align="right">{formatCurrency(line.credit)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                      <TableCell colSpan={2} align="right"><strong>Totales</strong></TableCell>
                      <TableCell align="right"><strong>{formatCurrency(row.total_debit)}</strong></TableCell>
                      <TableCell align="right"><strong>{formatCurrency(row.total_credit)}</strong></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
};

const JournalEntryList: React.FC = () => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEntries();
  }, []);

  const loadEntries = async () => {
    setLoading(true);
    try {
      const data = await journalEntriesService.getAll();
      // data podría venir paginado
      const list = Array.isArray(data) ? data : (data.results || []);
      setEntries(list);
    } catch (error) {
      console.error(error);
      toast.error('Error al cargar libro diario');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
            Libro Diario
        </Typography>
        <Paper>
            <TableContainer>
                <Table aria-label="collapsible table">
                    <TableHead>
                        <TableRow>
                            <TableCell />
                            <TableCell>Fecha</TableCell>
                            <TableCell>Número</TableCell>
                            <TableCell>Descripción</TableCell>
                            <TableCell align="right">Débitos</TableCell>
                            <TableCell align="right">Créditos</TableCell>
                            <TableCell align="center">Estado</TableCell>
                            <TableCell align="center">Origen</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {loading ? (
                             <TableRow>
                                <TableCell colSpan={8} align="center">
                                  <CircularProgress /> Cargando Asientos...
                                </TableCell>
                              </TableRow>
                        ) : entries.length === 0 ? (
                             <TableRow>
                                <TableCell colSpan={8} align="center">
                                  No hay movimientos registrados.
                                </TableCell>
                              </TableRow>
                        ) : (
                            entries.map((entry) => (
                                <Row key={entry.id} row={entry} />
                            ))
                        )}
                    </TableBody>
                </Table>
            </TableContainer>
        </Paper>
    </Box>
  );
};

export default JournalEntryList;
