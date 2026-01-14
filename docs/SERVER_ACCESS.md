# Acceso al Servidor de Producción (Satori)

## Datos de Conexión
- **IP Pública:** 178.156.215.106
- **Usuario:** root
- **Puerto:** 22 (SSH)
- **Proveedor:** Hetzner
- **OS:** Ubuntu 24.04

## Cómo Conectar

### Opción 1: Script Automático
Ejecuta el archivo `CONNECT_SERVER.bat` que he creado en la raíz del proyecto.
```powershell
.\CONNECT_SERVER.bat
```

### Opción 2: Comando Manual
En cualquier terminal (PowerShell/CMD):
```powershell
ssh root@178.156.215.106
```

## Primer Acceso
La primera vez que te conectes, verás un mensaje como:
`The authenticity of host '178.156.215.106' can't be established.`
Debes escribir **`yes`** y presionar Enter.

## Solución de Problemas
- **Permission denied (publickey):** Significa que la llave SSH local no coincide con la de Hetzner. Verifica que `id_ed25519.pub` esté cargada en el panel de control.
