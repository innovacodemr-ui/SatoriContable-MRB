import React from 'react';
import { Box, Typography, List, ListItem, ListItemIcon, ListItemText, ListItemButton, Paper, Divider } from '@mui/material';
import {
  Settings as SettingsIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Receipt as ReceiptIcon,
  AccountBalance as BankIcon,
  Security as SecurityIcon,
  IntegrationInstructions as ApiIcon,
  Inventory as InventoryIcon
} from '@mui/icons-material';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';

const SettingsLayout: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const menuItems = [
        { text: 'Empresa', icon: <BusinessIcon />, path: '/settings/company' },
        { text: 'Resoluciones DIAN', icon: <ReceiptIcon />, path: '/settings/resolutions' },
        { text: 'Productos y Servicios', icon: <InventoryIcon />, path: '/settings/products' },
        { text: 'Usuarios y Permisos', icon: <PersonIcon />, path: '/settings/users' },
        { text: 'Centros de Costo', icon: <BankIcon />, path: '/settings/cost-centers' },
        { text: 'Certificado Digital', icon: <SecurityIcon />, path: '/settings/certificate' },
        { text: 'Integraciones', icon: <ApiIcon />, path: '/settings/integrations' },
    ];

    return (
        <Box sx={{ display: 'flex', height: '100%' }}>
            {/* Sidebar Settings Panel */}
            <Paper elevation={0} sx={{ width: 280, borderRight: '1px solid #e0e0e0', display: 'flex', flexDirection: 'column' }}>
                <Box p={3}>
                    <Typography variant="h6" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <SettingsIcon /> Configuración
                    </Typography>
                </Box>
                <Divider />
                <List component="nav">
                    {menuItems.map((item) => (
                        <ListItem key={item.text} disablePadding>
                             <ListItemButton 
                                selected={location.pathname === item.path}
                                onClick={() => navigate(item.path)}
                             >
                                <ListItemIcon sx={{ minWidth: 40 }}>
                                    {item.icon}
                                </ListItemIcon>
                                <ListItemText primary={item.text} />
                            </ListItemButton>
                        </ListItem>
                    ))}
                </List>
            </Paper>

            {/* Content Area */}
            <Box sx={{ flexGrow: 1, p: 4, bgcolor: '#f9fafb', overflow: 'auto' }}>
                <Paper sx={{ p: 4, minHeight: '80vh' }}>
                     <Outlet />
                </Paper>
            </Box>
        </Box>
    );
};

export default SettingsLayout;
