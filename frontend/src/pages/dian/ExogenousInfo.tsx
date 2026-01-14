import React, { useState, useEffect } from 'react';
import {
  Box, Paper, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  IconButton, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Grid
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { dianService } from '../../services/api';
import { toast } from 'react-toastify';

interface DianFormat {
  id?: number;
  code: string;
  name: string;
  version: number;
  valid_from: number;
}

interface DianConcept {
  id?: number;
  format: number;
  code: string;
  name: string;
  description: string;
}

const ExogenousInfo: React.FC = () => {
  const [formats, setFormats] = useState<DianFormat[]>([]);
  const [concepts, setConcepts] = useState<DianConcept[]>([]);
  const [selectedFormat, setSelectedFormat] = useState<DianFormat | null>(null);
  
  // Dialog states
  const [openFormatDialog, setOpenFormatDialog] = useState(false);
  const [editingFormat, setEditingFormat] = useState<DianFormat | null>(null);
  
  const [openConceptDialog, setOpenConceptDialog] = useState(false);
  const [editingConcept, setEditingConcept] = useState<DianConcept | null>(null);

  // Form states
  const [formatForm, setFormatForm] = useState<DianFormat>({ code: '', name: '', version: 1, valid_from: 2025 });
  const [conceptForm, setConceptForm] = useState<DianConcept>({ format: 0, code: '', name: '', description: '' });

  useEffect(() => {
    loadFormats();
  }, []);

  const loadFormats = async () => {
    try {
      const data = await dianService.getFormats();
      setFormats(Array.isArray(data) ? data : []);
    } catch (error) {
      toast.error('Error cargando formatos');
    }
  };

  const loadConcepts = async (formatId: number) => {
    try {
      const data = await dianService.getConcepts(formatId);
      setConcepts(Array.isArray(data) ? data : []);
    } catch (error) {
      // toast.error('Error cargando conceptos'); // Silenciar o manejar mejor
      console.error(error); 
    }
  };

  const handleSelectFormat = (format: DianFormat) => {
    setSelectedFormat(format);
    if (format.id) loadConcepts(format.id);
  };

  // --- Format Handlers ---
  const handleOpenFormatDialog = (format?: DianFormat) => {
    if (format) {
      setEditingFormat(format);
      setFormatForm(format);
    } else {
      setEditingFormat(null);
      setFormatForm({ code: '', name: '', version: 1, valid_from: 2025 });
    }
    setOpenFormatDialog(true);
  };

  const handleSaveFormat = async () => {
    try {
      if (editingFormat && editingFormat.id) {
        await dianService.updateFormat(editingFormat.id, formatForm);
        toast.success('Formato actualizado');
      } else {
        await dianService.createFormat(formatForm);
        toast.success('Formato creado');
      }
      setOpenFormatDialog(false);
      loadFormats();
    } catch (error) {
      toast.error('Error guardando formato');
    }
  };

  const handleDeleteFormat = async (id: number) => {
    if (confirm('¿Eliminar formato y todos sus conceptos?')) {
      try {
        await dianService.deleteFormat(id);
        loadFormats();
        if (selectedFormat?.id === id) {
            setSelectedFormat(null);
            setConcepts([]);
        }
        toast.success('Eliminado');
      } catch (e) { toast.error('Error al eliminar'); }
    }
  };

  // --- Concept Handlers ---
  const handleOpenConceptDialog = (concept?: DianConcept) => {
    if (!selectedFormat?.id) return;
    if (concept) {
      setEditingConcept(concept);
      setConceptForm(concept);
    } else {
      setEditingConcept(null);
      setConceptForm({ format: selectedFormat.id, code: '', name: '', description: '' });
    }
    setOpenConceptDialog(true);
  };

  const handleSaveConcept = async () => {
    try {
      if (editingConcept && editingConcept.id) {
        await dianService.updateConcept(editingConcept.id, conceptForm);
        toast.success('Concepto actualizado');
      } else {
        await dianService.createConcept(conceptForm);
        toast.success('Concepto creado');
      }
      setOpenConceptDialog(false);
      if (selectedFormat?.id) loadConcepts(selectedFormat.id);
    } catch (error) {
      toast.error('Error guardando concepto');
    }
  };

   const handleDeleteConcept = async (id: number) => {
    if (confirm('¿Eliminar concepto?')) {
      try {
        await dianService.deleteConcept(id);
        if (selectedFormat?.id) loadConcepts(selectedFormat.id);
        toast.success('Eliminado');
      } catch (e) { toast.error('Error al eliminar'); }
    }
  };


  return (
    <Box p={3}>
      <Typography variant="h5" gutterBottom>Medios Magnéticos (Exógena) - Configuración</Typography>
      
      <Grid container spacing={3}>
        {/* Left: Formats */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Formatos</Typography>
              <Button startIcon={<AddIcon />} variant="contained" onClick={() => handleOpenFormatDialog()}>
                Nuevo
              </Button>
            </Box>
            <TableContainer sx={{ maxHeight: 600 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                     <TableCell>Código</TableCell>
                     <TableCell>Nombre</TableCell>
                     <TableCell>Ver.</TableCell>
                     <TableCell>Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {formats.map((fmt) => (
                    <TableRow 
                      key={fmt.id} 
                      selected={selectedFormat?.id === fmt.id}
                      onClick={() => handleSelectFormat(fmt)}
                      sx={{ cursor: 'pointer', '&.Mui-selected': { bgcolor: 'action.selected' } }}
                      hover
                    >
                      <TableCell>{fmt.code}</TableCell>
                      <TableCell>{fmt.name}</TableCell>
                      <TableCell>{fmt.version}</TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleOpenFormatDialog(fmt); }}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                         <IconButton size="small" onClick={(e) => { e.stopPropagation(); handleDeleteFormat(fmt.id!); }}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Right: Concepts */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
             <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                 Conceptos {selectedFormat ? `(${selectedFormat.code})` : ''}
              </Typography>
              <Button 
                startIcon={<AddIcon />} 
                variant="contained" 
                onClick={() => handleOpenConceptDialog()}
                disabled={!selectedFormat}
              >
                Nuevo
              </Button>
            </Box>
            
            {selectedFormat ? (
               <TableContainer sx={{ maxHeight: 600 }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                     <TableCell>Código</TableCell>
                     <TableCell>Nombre</TableCell>
                     <TableCell>Acciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {concepts.map((cpt) => (
                    <TableRow key={cpt.id}>
                      <TableCell>{cpt.code}</TableCell>
                      <TableCell>{cpt.name}</TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => handleOpenConceptDialog(cpt)}>
                          <EditIcon fontSize="small" />
                        </IconButton>
                        <IconButton size="small" onClick={() => handleDeleteConcept(cpt.id!)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                  {concepts.length === 0 && (
                    <TableRow><TableCell colSpan={3}>No hay conceptos registrados</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            ) : (
              <Box p={4} textAlign="center">
                <Typography color="textSecondary">Seleccione un formato de la izquierda para ver sus conceptos.</Typography>
              </Box>
            )}
           
          </Paper>
        </Grid>
      </Grid>

      {/* Format Dialog */}
      <Dialog open={openFormatDialog} onClose={() => setOpenFormatDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingFormat ? 'Editar Formato' : 'Nuevo Formato'}</DialogTitle>
        <DialogContent>
          <Box pt={2} display="flex" flexDirection="column" gap={2}>
            <TextField label="Código Formato (ej: 1001)" fullWidth value={formatForm.code} onChange={(e) => setFormatForm({...formatForm, code: e.target.value})} />
            <TextField label="Nombre del Formato" fullWidth multiline rows={2} value={formatForm.name} onChange={(e) => setFormatForm({...formatForm, name: e.target.value})} />
            <Grid container spacing={2}>
                 <Grid item xs={6}>
                    <TextField label="Versión" type="number" fullWidth value={formatForm.version} onChange={(e) => setFormatForm({...formatForm, version: parseInt(e.target.value)})} />
                 </Grid>
                 <Grid item xs={6}>
                    <TextField label="Año Vigencia" type="number" fullWidth value={formatForm.valid_from} onChange={(e) => setFormatForm({...formatForm, valid_from: parseInt(e.target.value)})} />
                 </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFormatDialog(false)}>Cancelar</Button>
          <Button onClick={handleSaveFormat} variant="contained">Guardar</Button>
        </DialogActions>
      </Dialog>
      
       {/* Concept Dialog */}
      <Dialog open={openConceptDialog} onClose={() => setOpenConceptDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingConcept ? 'Editar Concepto' : 'Nuevo Concepto'}</DialogTitle>
        <DialogContent>
          <Box pt={2} display="flex" flexDirection="column" gap={2}>
            <TextField label="Código Concepto (ej: 5001)" fullWidth value={conceptForm.code} onChange={(e) => setConceptForm({...conceptForm, code: e.target.value})} />
            <TextField label="Nombre del Concepto" fullWidth multiline rows={2} value={conceptForm.name} onChange={(e) => setConceptForm({...conceptForm, name: e.target.value})} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenConceptDialog(false)}>Cancelar</Button>
          <Button onClick={handleSaveConcept} variant="contained">Guardar</Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

export default ExogenousInfo;