import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  ListSubheader,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  AccountBalance as AccountBalanceIcon,
  Receipt as ReceiptIcon,
  People as PeopleIcon,
  Description as DescriptionIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  ShoppingCart as ShoppingCartIcon,
  MoveToInbox as InboxIcon,
  PostAdd as PostAddIcon,
  MonetizationOn as MonetizationOnIcon,
  Badge as BadgeIcon,
  BarChart as BarChartIcon,
  Approval as ApprovalIcon,
  Assignment as AssignmentIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const drawerWidth = 260;

const MainLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const { logout, user, clientName } = useAuth();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <Toolbar sx={{ flexDirection: 'column', alignItems: 'flex-start', justifyContent: 'center', py: 1, minHeight: 80 }}>
        <Typography variant="h6" noWrap component="div" sx={{ fontWeight: 'bold' }}>
          {clientName || 'Satori Contable'}
        </Typography>
        {user && (
           <Typography variant="caption" noWrap component="div" sx={{ color: 'text.secondary', mt: 0.5, display: 'block' }}>
             {user.email}
           </Typography>
        )}
      </Toolbar>
      <Divider />
      
      <List>
        <ListItem disablePadding>
            <ListItemButton onClick={() => navigate('/')}>
              <ListItemIcon><DashboardIcon /></ListItemIcon>
              <ListItemText primary="Dashboard" />
            </ListItemButton>
        </ListItem>
      </List>

      <Divider />

      <List
        subheader={
          <ListSubheader component="div" id="nested-list-subheader-sales">
            Ventas y Facturación
          </ListSubheader>
        }
      >
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/dian/documents')}>
            <ListItemIcon><ApprovalIcon /></ListItemIcon>
            <ListItemText primary="Facturación Electrónica" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/accounting/receivables')}>
             <ListItemIcon><AssignmentIcon /></ListItemIcon>
             <ListItemText primary="Cuentas por Cobrar" />
           </ListItemButton>
         </ListItem>
      </List>

      <Divider />

      <List
        subheader={
          <ListSubheader component="div" id="nested-list-subheader-radian">
            Recepción (RADIAN)
          </ListSubheader>
        }
      >
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/dian/inbox')}>
            <ListItemIcon><InboxIcon /></ListItemIcon>
            <ListItemText primary="Buzón de Facturas" />
          </ListItemButton>
        </ListItem>
      </List>

      <Divider />

      <List
        subheader={
          <ListSubheader component="div" id="nested-list-subheader-purchases">
            Compras y Gastos
          </ListSubheader>
        }
      >
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/purchases/support-documents')}>
            <ListItemIcon><DescriptionIcon /></ListItemIcon>
            <ListItemText primary="Documentos Soporte" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/purchases/suppliers')}>
            <ListItemIcon><PeopleIcon /></ListItemIcon>
            <ListItemText primary="Proveedores" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/accounting/payables')}>
             <ListItemIcon><AssignmentIcon /></ListItemIcon>
             <ListItemText primary="Cuentas por Pagar" />
           </ListItemButton>
         </ListItem>
      </List>

      <Divider />

      <List
        subheader={
          <ListSubheader component="div" id="nested-list-subheader-payroll">
            Nómina
          </ListSubheader>
        }
      >
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/payroll/dashboard')}>
            <ListItemIcon><BadgeIcon /></ListItemIcon>
            <ListItemText primary="Dashboard Nómina" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/payroll/novelties')}>
            <ListItemIcon><PostAddIcon /></ListItemIcon>
            <ListItemText primary="Novedades" />
          </ListItemButton>
        </ListItem>
      </List>

      <Divider />

      <List
         subheader={
          <ListSubheader component="div" id="nested-list-subheader-accounting">
            Contabilidad
          </ListSubheader>
        }
      >
        <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/accounting/journal-entries')}>
             <ListItemIcon><ReceiptIcon /></ListItemIcon>
             <ListItemText primary="Libro Diario" />
           </ListItemButton>
         </ListItem>
         <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/accounting/accounts')}>
             <ListItemIcon><AccountBalanceIcon /></ListItemIcon>
             <ListItemText primary="Plan de Cuentas" />
           </ListItemButton>
         </ListItem>
         <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/accounting/third-parties')}>
             <ListItemIcon><PeopleIcon /></ListItemIcon>
             <ListItemText primary="Terceros (General)" />
           </ListItemButton>
         </ListItem>
         <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/accounting/templates')}>
             <ListItemIcon><PostAddIcon /></ListItemIcon>
             <ListItemText primary="Config. Plantillas" />
           </ListItemButton>
         </ListItem>
         <ListItem disablePadding>
           <ListItemButton onClick={() => navigate('/dian/exogenous')}>
             <ListItemIcon><AssignmentIcon /></ListItemIcon>
             <ListItemText primary="Exógena" />
           </ListItemButton>
         </ListItem>
      </List>
      
      <Divider />

      <List
        subheader={
          <ListSubheader component="div" id="nested-list-subheader-treasury">
            Tesorería
          </ListSubheader>
        }
      >
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/treasury/payments')}>
            <ListItemIcon><MonetizationOnIcon /></ListItemIcon>
            <ListItemText primary="Pagos (Egresos)" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/treasury/banks')}>
            <ListItemIcon><AccountBalanceIcon /></ListItemIcon>
            <ListItemText primary="Bancos" />
          </ListItemButton>
        </ListItem>
      </List>

      <Divider />
      
      <List
        subheader={
          <ListSubheader component="div" id="nested-list-subheader-reports">
            Reportes
          </ListSubheader>
        }
      >
         <ListItem disablePadding>
            <ListItemButton onClick={() => navigate('/reports')}>
              <ListItemIcon><BarChartIcon /></ListItemIcon>
              <ListItemText primary="Reportes Financieros" />
            </ListItemButton>
         </ListItem>
      </List>

      <Divider />
      
      <List>
         <ListItem disablePadding>
            <ListItemButton onClick={() => navigate('/settings')}>
              <ListItemIcon><SettingsIcon /></ListItemIcon>
              <ListItemText primary="Configuración" />
            </ListItemButton>
         </ListItem>
         <ListItem disablePadding>
            <ListItemButton onClick={logout}>
              <ListItemIcon><LogoutIcon /></ListItemIcon>
              <ListItemText primary="Cerrar Sesión" />
            </ListItemButton>
         </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {clientName ? `${clientName} | Sistema Contable` : 'Sistema Contable - Cali, Colombia'}
          </Typography>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          backgroundColor: '#f5f5f5',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
