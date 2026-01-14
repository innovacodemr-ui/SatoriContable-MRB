import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Layouts
import MainLayout from './layouts/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import InitialSetup from './pages/InitialSetup';
import Accounts from './pages/accounting/Accounts';
import JournalEntries from './pages/accounting/JournalEntries';
import TemplateBuilder from './pages/accounting/TemplateBuilder';
import ThirdParties from './pages/accounting/ThirdParties';
import AccountsReceivable from './pages/accounting/AccountsReceivable';
import AccountsPayable from './pages/accounting/AccountsPayable';
import InvoiceForm from './pages/invoicing/InvoiceForm';
import Settings from './pages/Settings'; // Reutilizamos la pagina completa de configuracion

// Suprimir warnings de React Router en desarrollo
if (import.meta.env.DEV) {
  const originalWarn = console.warn;
  console.warn = (...args: any[]) => {
    if (typeof args[0] === 'string' && args[0].includes('React Router Future Flag')) {
      return;
    }
    originalWarn.apply(console, args);
  };
}
import ElectronicDocuments from './pages/dian/ElectronicDocuments';
import InvoiceInbox from './pages/dian/InvoiceInbox';
import ExogenousInfo from './pages/dian/ExogenousInfo';
import Reports from './pages/reports/Reports';
// import Settings from './pages/Settings';
import Login from './pages/Login';
import NoveltyRegistrationForm from './pages/payroll/NoveltyRegistrationForm';
import PayrollDashboard from './pages/payroll/PayrollDashboard';

import SupportDocumentList from './pages/purchases/SupportDocumentList';
import SupportDocumentForm from './pages/purchases/SupportDocumentForm';

import BankAccountList from './pages/treasury/banks/BankAccountList';
import PaymentList from './pages/treasury/payments/PaymentList';
import PaymentForm from './pages/treasury/payments/PaymentForm';

import SettingsLayout from './pages/settings/SettingsLayout';
import ResolutionsManager from './pages/settings/company/ResolutionsManager';
import CostCentersManager from './pages/settings/accounting/CostCentersManager';
import ProductsManager from './pages/settings/inventory/ProductsManager';



// Theme configuration
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
});

import { AuthProvider } from './context/AuthContext';
import PrivateRoute from './components/PrivateRoute';

const App: React.FC = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            {/* Ruta para callback de autenticación social */}
            <Route path="/auth/callback" element={<div>Procesando autenticación...</div>} />

            <Route element={<PrivateRoute />}>
              <Route path="/" element={<MainLayout />}>
                <Route index element={<Dashboard />} />
                <Route path="setup" element={<InitialSetup />} />

                {/* Contabilidad */}
                <Route path="accounting/accounts" element={<Accounts />} />
                <Route path="accounting/journal-entries" element={<JournalEntries />} />
                <Route path="accounting/templates" element={<TemplateBuilder />} />
                <Route path="accounting/third-parties" element={<ThirdParties />} />
                <Route path="accounting/receivables" element={<AccountsReceivable />} />
                <Route path="accounting/payables" element={<AccountsPayable />} />
                {/* Compras */}
                <Route path="purchases/support-documents" element={<SupportDocumentList />} />
                <Route path="purchases/support-documents/new" element={<SupportDocumentForm />} />
                <Route path="purchases/support-documents/:id" element={<SupportDocumentForm />} />
                <Route path="purchases/suppliers" element={<ThirdParties partyType="PROVEEDOR" />} />

                {/* Tesorería */}
                <Route path="treasury/banks" element={<BankAccountList />} />
                <Route path="treasury/payments" element={<PaymentList />} />
                <Route path="treasury/payments/new" element={<PaymentForm />} />
                <Route path="treasury/payments/:id" element={<PaymentForm />} />

                {/* Facturación Electrónica DIAN */}
                <Route path="dian/documents" element={<ElectronicDocuments />} />
                <Route path="dian/documents/new" element={<InvoiceForm />} />
                <Route path="dian/inbox" element={<InvoiceInbox />} />
                <Route path="dian/exogenous" element={<ExogenousInfo />} />

                {/* Reportes */}
                <Route path="reports" element={<Reports />} />

                {/* Nómina */}
                <Route path="payroll/novelties" element={<NoveltyRegistrationForm />} />
                <Route path="payroll/dashboard" element={<PayrollDashboard />} />

                {/* Configuración */}
                <Route path="settings" element={<SettingsLayout />}>
                  <Route index element={<Settings />} /> {/* Default to General Settings */}
                  <Route path="company" element={<Settings />} />
                  <Route path="resolutions" element={<ResolutionsManager />} />
                  <Route path="products" element={<ProductsManager />} />
                  <Route path="users" element={<div>Usuarios (Próximamente)</div>} />
                  <Route path="cost-centers" element={<CostCentersManager />} />
                  <Route path="certificate" element={<Settings />} />
                  <Route path="integrations" element={<div>Integraciones (Próximamente)</div>} />
                </Route>
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </Router>
      <ToastContainer position="top-right" autoClose={3000} />
    </ThemeProvider>
  );
};

export default App;
