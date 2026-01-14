import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Autocomplete,
  Grid,
  Chip,
  Dialog,
  AppBar,
  Toolbar,
  Slide
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { TransitionProps } from '@mui/material/transitions';
import { toast } from 'react-toastify';
import { 
  accountingTemplatesService, 
  accountingDocumentTypesService, 
  accountsService 
} from '../../services/api';

// --- Interfaces ---

interface Account {
  id: number;
  code: string;
  name: string;
  nature: string;
}

interface DocumentType {
  id: number;
  code: string;
  name: string;
}

interface TemplateLine {
  id?: number;
  account: number | null; // ID of the account
  account_obj?: Account; // For UI display (Autocomplete)
  nature: 'DEBITO' | 'CREDITO';
  calculation_method: 'FIXED_VALUE' | 'PERCENTAGE_OF_SUBTOTAL' | 'PERCENTAGE_OF_TOTAL' | 'PERCENTAGE_OF_TAX' | 'PLUG';
  value: number;
  description_template: string;
}

interface Template {
  id?: number;
  name: string;
  document_type: number | string; // ID
  active: boolean;
  lines: TemplateLine[];
}

// --- Transition for Full Screen Dialog ---
const Transition = React.forwardRef(function Transition(
  props: TransitionProps & {
    children: React.ReactElement;
  },
  ref: React.Ref<unknown>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

const TemplateBuilder: React.FC = () => {
  // State for Lists
  // Cache busting comment: v2
  const [templates, setTemplates] = useState<Template[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [docTypes, setDocTypes] = useState<DocumentType[]>([]);
  const [loading, setLoading] = useState(false);

  // State for Form
  const [openEditor, setOpenEditor] = useState(false);
  const [currentTemplate, setCurrentTemplate] = useState<Template>({
    name: '',
    document_type: '',
    active: true,
    lines: []
  });

  // Load Data
  useEffect(() => {
    fetchTemplates();
    fetchAuxiliaryData();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const data = await accountingTemplatesService.getAll();
      setTemplates(data);
    } catch (error) {
      console.error(error);
      toast.error('Error cargando plantillas');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuxiliaryData = async () => {
    try {
      const [accData, docData] = await Promise.all([
        accountsService.getAll(),
        accountingDocumentTypesService.getAll()
      ]);
      setAccounts(accData);
      setDocTypes(docData);
    } catch (error) {
      console.error(error);
      toast.error('Error cargando datos auxiliares');
    }
  };

  // --- Form Handlers ---

  const handleCreateNew = () => {
    setCurrentTemplate({
      name: '',
      document_type: docTypes.length > 0 ? docTypes[0].id : '',
      active: true,
      lines: []
    });
    setOpenEditor(true);
  };

  const handleEdit = async (templateId: number) => {
    try {
      const template = await accountingTemplatesService.getById(templateId);
      // Map inner lines to have account objects if needed or ensure format
      // Note: Backend might return account_id and account_code separately.
      // We assume serializer returns 'account' as ID and maybe 'account_detail' or we map it.
      // Let's assume standard DRF serializer. We might need to match account ID to our accounts list to pre-fill Autocomplete.
      
      const mappedLines = template.lines.map((line: any) => ({
        ...line,
        account_obj: accounts.find(a => a.id === line.account) || null
      }));

      setCurrentTemplate({ ...template, lines: mappedLines });
      setOpenEditor(true);
    } catch (error) {
      console.error(error);
      toast.error('Error cargando detalle de plantilla');
    }
  };

  const handleCloseEditor = () => {
    setOpenEditor(false);
  };

  const handleSave = async () => {
    try {
        // Validation
        if (!currentTemplate.name) {
            toast.warning('El nombre es obligatorio');
            return;
        }
        if (currentTemplate.lines.length === 0) {
            toast.warning('Debe agregar al menos una línea');
            return;
        }

        // Prepare payload
        const payload = {
            ...currentTemplate,
            lines: currentTemplate.lines.map(line => ({
                id: line.id, // Include ID for updates
                account: line.account_obj?.id,
                nature: line.nature,
                calculation_method: line.calculation_method,
                value: line.value,
                description_template: line.description_template
            }))
        };

        if (currentTemplate.id) {
            await accountingTemplatesService.update(currentTemplate.id, payload);
            toast.success('Plantilla actualizada');
        } else {
            await accountingTemplatesService.create(payload);
            toast.success('Plantilla creada');
        }
        setOpenEditor(false);
        fetchTemplates();
    } catch (error) {
        console.error(error);
        toast.error('Error guardando plantilla');
    }
  };

  // --- Line Editors ---

  const addLine = () => {
    setCurrentTemplate(prev => ({
        ...prev,
        lines: [
            ...prev.lines,
            {
                account: null,
                nature: 'DEBITO',
                calculation_method: 'FIXED_VALUE',
                value: 0,
                description_template: ''
            }
        ]
    }));
  };

  const removeLine = (index: number) => {
    const newLines = [...currentTemplate.lines];
    newLines.splice(index, 1);
    setCurrentTemplate(prev => ({ ...prev, lines: newLines }));
  };

  const updateLine = (index: number, field: keyof TemplateLine, value: any) => {
    const newLines = [...currentTemplate.lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setCurrentTemplate(prev => ({ ...prev, lines: newLines }));
  };

  // --- Render ---

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Plantillas Contables</Typography>
        <Button 
            variant="contained" 
            startIcon={<AddIcon />} 
            onClick={handleCreateNew}
        >
            Nueva Plantilla
        </Button>
      </Box>

      {/* Template List */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Tipo Documento</TableCell>
              <TableCell>Activa</TableCell>
              <TableCell>Acciones</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {templates.map((tpl) => (
              <TableRow key={tpl.id}>
                <TableCell>{tpl.name}</TableCell>
                <TableCell>
                    {/* Display Document Type Name */}
                    {typeof tpl.document_type === 'object' 
                        ? (tpl.document_type as any).name 
                        : docTypes.find(d => d.id === tpl.document_type)?.name || tpl.document_type}
                </TableCell>
                <TableCell>
                    <Chip 
                        label={tpl.active ? "Si" : "No"} 
                        color={tpl.active ? "success" : "default"} 
                        size="small" 
                    />
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => tpl.id && handleEdit(tpl.id)}>
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {templates.length === 0 && !loading && (
                <TableRow>
                    <TableCell colSpan={4} align="center">No hay plantillas configuradas</TableCell>
                </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Full Screen Editor Dialog */}
      <Dialog
        fullScreen
        open={openEditor}
        onClose={handleCloseEditor}
        TransitionComponent={Transition}
      >
        <AppBar sx={{ position: 'relative' }}>
          <Toolbar>
            <IconButton
              edge="start"
              color="inherit"
              onClick={handleCloseEditor}
              aria-label="close"
            >
              <ArrowBackIcon />
            </IconButton>
            <Typography sx={{ ml: 2, flex: 1 }} variant="h6" component="div">
              {currentTemplate.id ? 'Editar Plantilla' : 'Nueva Plantilla'}
            </Typography>
            <Button autoFocus color="inherit" onClick={handleSave} startIcon={<SaveIcon />}>
              Guardar
            </Button>
          </Toolbar>
        </AppBar>
        
        <Box p={3} sx={{ maxWidth: 1200, margin: '0 auto', width: '100%' }}>
            
            {/* Header Form */}
            <Paper sx={{ p: 3, mb: 3 }}>
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            label="Nombre de la Plantilla"
                            value={currentTemplate.name}
                            onChange={(e) => setCurrentTemplate({...currentTemplate, name: e.target.value})}
                        />
                    </Grid>
                    <Grid item xs={12} md={4}>
                         <FormControl fullWidth>
                            <InputLabel>Tipo de Documento</InputLabel>
                            <Select
                                value={currentTemplate.document_type}
                                label="Tipo de Documento"
                                onChange={(e) => setCurrentTemplate({...currentTemplate, document_type: e.target.value})}
                            >
                                {docTypes.map(dt => (
                                    <MenuItem key={dt.id} value={dt.id}>
                                        {dt.code} - {dt.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={2}>
                        <FormControlLabel
                            control={
                                <Switch 
                                    checked={currentTemplate.active} 
                                    onChange={(e) => setCurrentTemplate({...currentTemplate, active: e.target.checked})} 
                                />
                            }
                            label="Activa"
                        />
                    </Grid>
                </Grid>
            </Paper>

            {/* Lines Editor */}
            <Paper sx={{ p: 3 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">Líneas Contables</Typography>
                    <Button startIcon={<AddIcon />} onClick={addLine} variant="outlined">
                        Agregar Línea
                    </Button>
                </Box>
                
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell width="30%">Cuenta</TableCell>
                                <TableCell width="15%">Naturaleza</TableCell>
                                <TableCell width="15%">Método</TableCell>
                                <TableCell width="10%">Valor</TableCell>
                                <TableCell width="25%">Descripción</TableCell>
                                <TableCell width="5%"></TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {currentTemplate.lines.map((line, index) => (
                                <TableRow key={index}>
                                    <TableCell>
                                        <Autocomplete
                                            options={accounts}
                                            getOptionLabel={(option) => `${option.code} - ${option.name}`}
                                            value={line.account_obj || null}
                                            onChange={(_, newValue) => updateLine(index, 'account_obj', newValue)}
                                            renderInput={(params) => <TextField {...params} variant="standard" />}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Select
                                            fullWidth
                                            variant="standard"
                                            value={line.nature}
                                            onChange={(e) => updateLine(index, 'nature', e.target.value)}
                                        >
                                            <MenuItem value="DEBITO">Débito</MenuItem>
                                            <MenuItem value="CREDITO">Crédito</MenuItem>
                                        </Select>
                                    </TableCell>
                                    <TableCell>
                                        <Select
                                            fullWidth
                                            variant="standard"
                                            value={line.calculation_method}
                                            onChange={(e) => updateLine(index, 'calculation_method', e.target.value)}
                                        >
                                            <MenuItem value="FIXED_VALUE">Valor Fijo</MenuItem>
                                            <MenuItem value="PERCENTAGE_OF_SUBTOTAL">% del Subtotal</MenuItem>
                                            <MenuItem value="PERCENTAGE_OF_TOTAL">% del Total</MenuItem>
                                            <MenuItem value="PERCENTAGE_OF_TAX">% del Impuesto</MenuItem>
                                            <MenuItem value="PLUG">Diferencia (Plug)</MenuItem>
                                        </Select>
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            type="number"
                                            fullWidth
                                            variant="standard"
                                            value={line.value}
                                            onChange={(e) => updateLine(index, 'value', parseFloat(e.target.value))}
                                            disabled={line.calculation_method === 'PLUG'}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <TextField
                                            fullWidth
                                            variant="standard"
                                            value={line.description_template}
                                            onChange={(e) => updateLine(index, 'description_template', e.target.value)}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <IconButton size="small" color="error" onClick={() => removeLine(index)}>
                                            <DeleteIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

            </Paper>
        </Box>
      </Dialog>
    </Box>
  );
};

export default TemplateBuilder;
