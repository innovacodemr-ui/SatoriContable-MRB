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
  Tooltip,
} from '@mui/material';
import { Add as AddIcon, Send as SendIcon, Visibility as VisibilityIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import purchasesService, { SupportDocument } from '../../services/purchasesService';

const SupportDocumentList: React.FC = () => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<SupportDocument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const data = await purchasesService.getSupportDocuments();
      // data might be wrapped in paginated response? 
      // Assuming list or results array. If drf ViewSet list is used without pagination it returns list. 
      // If paginated, data.results.
      // Let's assume list for now as per MVP simplicity, or check response structure. 
      // Safest is to check if Array.isArray(data) else data.results
      const list = Array.isArray(data) ? data : (data.results || []);
      setDocuments(list);
    } catch (error) {
      console.error("Error loading documents", error);
    } finally {
      setLoading(false);
    }
  };

  const handleTransmit = async (id: number) => {
    try {
      await purchasesService.transmitToDian(id);
      loadDocuments(); // Reload to update status
    } catch (error) {
      console.error("Error transmitting document", error);
      alert("Error al transmitir documento. Ver consola.");
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Documentos Soporte
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/purchases/support-documents/new')}
        >
          Nuevo Documento
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Fecha</TableCell>
              <TableCell>Consecutivo</TableCell>
              <TableCell>Proveedor</TableCell>
              <TableCell align="right">Total</TableCell>
              <TableCell align="center">Estado</TableCell>
              <TableCell align="right">Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No hay documentos registrados.
                </TableCell>
              </TableRow>
            )}
            {documents.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell>{doc.issue_date}</TableCell>
                <TableCell>{doc.consecutive || 'N/A'}</TableCell>
                <TableCell>{doc.supplier_name || 'Desconocido'}</TableCell>
                <TableCell align="right">
                  {new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(doc.total_amount))}
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={doc.status === 'SENT_DIAN' ? 'Enviado DIAN' : 'Borrador'}
                    color={doc.status === 'SENT_DIAN' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Ver Detalle / Editar">
                     <IconButton size="small" onClick={() => navigate(`/purchases/support-documents/${doc.id}`)}>
                        <VisibilityIcon />
                     </IconButton>
                  </Tooltip>
                  {doc.status !== 'SENT_DIAN' && (
                    <Tooltip title="Transmitir a DIAN">
                      <IconButton 
                        size="small" 
                        color="primary" 
                        onClick={() => handleTransmit(doc.id!)}
                      >
                        <SendIcon />
                      </IconButton>
                    </Tooltip>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default SupportDocumentList;
