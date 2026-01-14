import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  MenuItem,
  Button,
  Grid,
  Alert,
  Paper,
  CircularProgress,
  InputLabel,
  FormControl,
  Select,
  SelectChangeEvent
} from '@mui/material';
import { payrollService } from '../../services/api';
import { addDays, parseISO, format } from 'date-fns';

interface Employee {
  id: number;
  code: string;
  third_party: {
    first_name: string;
    surname: string;
  };
}

interface NoveltyType {
  code: string; // The code we send (e.g. 'VAC', 'IGE_66')
  name: string;
}

const NoveltyRegistrationForm: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [noveltyTypes, setNoveltyTypes] = useState<NoveltyType[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Form State
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [selectedNoveltyType, setSelectedNoveltyType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [days, setDays] = useState<number | ''>('');
  const [endDate, setEndDate] = useState('');
  const [file, setFile] = useState<File | null>(null);

  // Feedback State
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadCatalogs();
  }, []);

  const loadCatalogs = async () => {
    try {
      const [empData, typesData] = await Promise.all([
        payrollService.getEmployees(),
        payrollService.getNoveltyTypes()
      ]);
      setEmployees(empData.results || empData); // Handle pagination or list
      setNoveltyTypes(typesData.results || typesData);
    } catch (err) {
      console.error("Error loading catalogs", err);
      setError("Error al cargar listados. Verifique su conexión.");
    }
  };

  // Smart Date Calculation
  useEffect(() => {
    if (startDate && days) {
      try {
        const start = parseISO(startDate);
        // Logic: start date counts as day 1. So add (days - 1).
        const end = addDays(start, Number(days) - 1);
        setEndDate(format(end, 'yyyy-MM-dd'));
      } catch (e) {
        // Invalid date
      }
    }
  }, [startDate, days]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    if (!selectedEmployee || !selectedNoveltyType || !startDate || !days) {
      setError("Por favor complete todos los campos obligatorios.");
      setLoading(false);
      return;
    }

    const formData = new FormData();
    formData.append('employee', selectedEmployee);
    formData.append('novelty_code', selectedNoveltyType); // Backend expects 'novelty_code'
    formData.append('start_date', startDate);
    formData.append('days', days.toString());
    
    // We can also send end_date implicit or explicit. The backend calculates it too, 
    // but sending the one calculated ensures UX match.
    // However, the backend logic I saw earlier calculates it too or takes data.
    // Let's rely on backend calculation or send it if required. 
    // The previous test verified backend calculation, so I can omit end_date or send it.
    // I'll omit it to let backend source of truth rule, or send for validation.
    // Actually, in the test 'end_date' was in response, not input. 
    // Wait, in `test_create_novelty_overlap_error`, input was `days`.
    
    if (file) {
      formData.append('attachment', file);
    }

    try {
      await payrollService.createNovelty(formData);
      setSuccess("Novedad registrada exitosamente.");
      // Reset form
      setFile(null);
      setDays('');
      setStartDate('');
      setEndDate('');
      // Keep employee/type selected for speed? Or reset. Let's reset type.
      setSelectedNoveltyType('');
    } catch (err: any) {
      console.error(err);
      if (err.response && err.response.status === 400) {
        // Extract useful error message from DRF response
        // DRF returns { field: [errors], ... } or [errors]
        const data = err.response.data;
        let msg = "Error de validación.";
        if (typeof data === 'object') {
           // Try to find non_field_errors or specific fields
           const parts = [];
           for (const key in data) {
             const val = Array.isArray(data[key]) ? data[key].join(' ') : data[key];
             parts.push(`${key}: ${val}`);
           }
           msg = parts.join(' | ');
        }
        setError(`Error 400: ${msg}`);
      } else {
        setError("Error inesperado al guardar la novedad.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 4, maxWidth: 800, mx: 'auto', mt: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom>
        Registro de Novedades
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          
          {/* Employee Selector */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Empleado</InputLabel>
              <Select
                value={selectedEmployee}
                label="Empleado"
                onChange={(e: SelectChangeEvent) => setSelectedEmployee(e.target.value)}
              >
                {employees.map((emp) => (
                  <MenuItem key={emp.id} value={emp.id}>
                    {emp.code} - {emp.third_party.first_name} {emp.third_party.surname}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Novelty Type Selector */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Tipo de Novedad</InputLabel>
              <Select
                value={selectedNoveltyType}
                label="Tipo de Novedad"
                onChange={(e: SelectChangeEvent) => setSelectedNoveltyType(e.target.value)}
              >
                {noveltyTypes.map((type) => (
                  <MenuItem key={type.code} value={type.code}>
                    {type.code} - {type.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Dates Section */}
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Fecha Inicio"
              type="date"
              InputLabelProps={{ shrink: true }}
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Días"
              type="number"
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              inputProps={{ min: 1 }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Fecha Fin (Calc)"
              type="date"
              value={endDate}
              InputLabelProps={{ shrink: true }}
              disabled
              helperText="Calculado automáticamente"
            />
          </Grid>

          {/* File Upload */}
          <Grid item xs={12}>
             <Button
              variant="outlined"
              component="label"
              fullWidth
             >
              {file ? file.name : "Subir Soporte (PDF/Img)"}
              <input
                type="file"
                hidden
                onChange={handleFileChange}
                accept=".pdf,image/*"
              />
             </Button>
          </Grid>

          {/* Actions */}
          <Grid item xs={12}>
            <Button 
              type="submit" 
              variant="contained" 
              color="primary" 
              size="large"
              fullWidth
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : "Registrar Novedad"}
            </Button>
          </Grid>

        </Grid>
      </form>
    </Paper>
  );
};

export default NoveltyRegistrationForm;
