# Protocolo de Desarrollo Satori - Multi-Tenant Security

## Roles de Inteligencia Artificial
1. **Constructor (Jules / Gemini Code Assist):** - Responsable de la implementación técnica y refactorización.
   - Debe seguir el "Plan de Remediación de Multi-Tenancy" para añadir ForeignKey(client) en todos los modelos de accounting, invoicing y payroll.
   - Debe priorizar la limpieza del código y la compatibilidad con Django.

2. **Supervisor (Antigravity-Audit / Deep Think):**
   - Responsable de auditoría de seguridad y pruebas de estrés.
   - Su objetivo es encontrar fallos en el aislamiento de datos (Data Leaks).
   - Ningún cambio en los modelos se considera final sin su informe de "Aislamiento Exitoso".

## Reglas de Oro
- **Aislamiento Total:** Ninguna consulta a la base de datos debe ejecutarse sin un filtro de `client_id` activo.
- **Validación Cruzada:** Jules propone el código; Antigravity-Audit intenta romperlo.
- **Portero Infalible:** El middleware debe asegurar el contexto del tenant antes de llegar a la capa de vistas (API).
