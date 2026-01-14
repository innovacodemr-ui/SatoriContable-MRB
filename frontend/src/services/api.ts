/**
 * Servicio de API - Abstracción para Web y Desktop
 * Detecta automáticamente el entorno y usa la fuente de datos correcta
 */

import axios from 'axios';

// Configuración base
// En producción, usamos rutas relativas para aprovechar el proxy de Nginx y evitar problemas de Mixed Content
const API_BASE_URL = import.meta.env.VITE_API_URL || 
                     (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

// Detectar si estamos en Electron
const isDesktop = () => {
  return window.electronAPI?.isDesktop === true;
};

// Cliente HTTP para web
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token y contexto de tenant
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  const clientId = localStorage.getItem('client_id');
  if (clientId) {
      config.headers['X-Client-Id'] = clientId;
  }

  return config;
});

// Interceptor para manejar errores 401 (Token vencido o inválido)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn('Sesión expirada o no autorizada. Cerrando sesión...');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('client_id');
      localStorage.removeItem('user');
      // Redirigir al login si no estamos ya allí
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Servicio de Cuentas (PUC)
 */
// Servicios de Core
export const coreService = {
  getDashboardStats: async () => {
    if (isDesktop()) {
      return (await window.electronAPI!.invoke('get-dashboard-stats'));
    }
    const response = await apiClient.get('/core/dashboard-stats/');
    return response.data;
  }
};

export const accountsService = {
  /**
   * Obtener todas las cuentas
   */
  async getAll(filters = {}) {
    if (isDesktop()) {
      // Desktop: usar SQLite local
      const result = await window.db.getAccounts(filters);
      return result.data || [];
    } else {
      // Web: usar API Django
      const response = await apiClient.get('/accounting/accounts/', { params: filters });
      // Manejar respuesta paginada o lista directa
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  /**
   * Obtener una cuenta por ID
   */
  async getById(id) {
    if (isDesktop()) {
      const result = await window.electronAPI.dbQuery(
        'SELECT * FROM accounts WHERE id = ?',
        [id]
      );
      return result.data?.[0];
    } else {
      const response = await apiClient.get(`/accounting/accounts/${id}/`);
      return response.data;
    }
  },

  /**
   * Crear nueva cuenta
   */
  async create(account) {
    if (isDesktop()) {
      const result = await window.db.createAccount(account);
      return result.data;
    } else {
      const response = await apiClient.post('/accounting/accounts/', account);
      return response.data;
    }
  },

  /**
   * Actualizar cuenta
   */
  async update(id, account) {
    if (isDesktop()) {
      const result = await window.db.updateAccount(id, account);
      return result.data;
    } else {
      const response = await apiClient.put(`/accounting/accounts/${id}/`, account);
      return response.data;
    }
  },

  /**
   * Eliminar cuenta
   */
  async delete(id) {
    if (isDesktop()) {
      const result = await window.electronAPI.dbQuery(
        'DELETE FROM accounts WHERE id = ?',
        [id]
      );
      return result.success;
    } else {
      await apiClient.delete(`/accounting/accounts/${id}/`);
      return true;
    }
  },

  /**
   * Obtener balance de una cuenta
   */
  async getBalance(id, startDate, endDate) {
    if (isDesktop()) {
      const sql = `
        SELECT 
          COALESCE(SUM(debit), 0) as total_debit,
          COALESCE(SUM(credit), 0) as total_credit
        FROM journal_entry_lines
        WHERE account_id = ?
        AND journal_entry_id IN (
          SELECT id FROM journal_entries 
          WHERE status = 'POSTED'
          AND date BETWEEN ? AND ?
        )
      `;
      const result = await window.electronAPI.dbQuery(sql, [id, startDate, endDate]);
      const data = result.data?.[0] || {};
      return {
        debit: data.total_debit || 0,
        credit: data.total_credit || 0,
        balance: (data.total_debit || 0) - (data.total_credit || 0)
      };
    } else {
      const response = await apiClient.get(`/accounting/accounts/${id}/balance/`, {
        params: { start_date: startDate, end_date: endDate }
      });
      return response.data;
    }
  }
};

/** * Servicio DIAN (Formatos y Conceptos)
 */
export const dianService = {
  async getFormats() {
    if (isDesktop()) {
      const result = await window.db.getDianFormats();
      return result.data || [];
    } else {
      const response = await apiClient.get('/accounting/dian-formats/');
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  async createFormat(data) {
    if (isDesktop()) {
      const result = await window.db.createDianFormat(data);
      return { ...data, id: result.lastId };
    } else {
      const response = await apiClient.post('/accounting/dian-formats/', data);
      return response.data;
    }
  },

  async updateFormat(id, data) {
    if (isDesktop()) {
      await window.db.updateDianFormat(id, data);
      return { ...data, id };
    } else {
      const response = await apiClient.put(`/accounting/dian-formats/${id}/`, data);
      return response.data;
    }
  },

  async deleteFormat(id) {
    if (isDesktop()) {
      await window.db.deleteDianFormat(id);
      return true;
    } else {
      await apiClient.delete(`/accounting/dian-formats/${id}/`);
      return true;
    }
  },

  async getConcepts(formatId?: number) {
    if (isDesktop()) {
      const result = await window.db.getDianConcepts(formatId);
      return result.data || [];
    } else {
      // Changed param from 'format' to 'dian_format' to avoid conflict with DRF format suffix
      const params = formatId ? { dian_format: formatId } : {}; 
      const response = await apiClient.get('/accounting/dian-concepts/', { params });
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  async createConcept(data) {
    if (isDesktop()) {
      const result = await window.db.createDianConcept(data);
      return { ...data, id: result.lastId };
    } else {
      const response = await apiClient.post('/accounting/dian-concepts/', data);
      return response.data;
    }
  },

  async updateConcept(id, data) {
    if (isDesktop()) {
      await window.db.updateDianConcept(id, data);
      return { ...data, id };
    } else {
      const response = await apiClient.put(`/accounting/dian-concepts/${id}/`, data);
      return response.data;
    }
  },

  async deleteConcept(id) {
    if (isDesktop()) {
      await window.db.deleteDianConcept(id);
      return true;
    } else {
      await apiClient.delete(`/accounting/dian-concepts/${id}/`);
      return true;
    }
  }
};

/** * Servicio de Terceros
 */
export const thirdPartiesService = {
  async getAll(filters = {}) {
    if (isDesktop()) {
      const result = await window.db.getThirdParties(filters);
      return result.data || [];
    } else {
      const response = await apiClient.get('/accounting/third-parties/', { params: filters });
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  async getById(id) {
    if (isDesktop()) {
      const result = await window.electronAPI.dbQuery(
        'SELECT * FROM third_parties WHERE id = ?',
        [id]
      );
      return result.data?.[0];
    } else {
      const response = await apiClient.get(`/accounting/third-parties/${id}/`);
      return response.data;
    }
  },

  async create(thirdParty) {
    if (isDesktop()) {
      const result = await window.db.createThirdParty(thirdParty);
      return result.data;
    } else {
      const response = await apiClient.post('/accounting/third-parties/', thirdParty);
      return response.data;
    }
  },

  async update(id, thirdParty) {
    if (isDesktop()) {
      const sql = `
        UPDATE third_parties 
        SET party_type = ?, person_type = ?, identification_type = ?, identification_number = ?, check_digit = ?,
            business_name = ?, trade_name = ?, first_name = ?, middle_name = ?, surname = ?, second_surname = ?,
            country_code = ?, department_code = ?, city_code = ?, postal_code = ?, address = ?,
            tax_regime = ?, fiscal_responsibilities = ?, ciiu_code = ?,
            phone = ?, email = ?, mobile = ?, is_customer = ?, is_supplier = ?,
            updated_at = datetime('now'), needs_sync = 1
        WHERE id = ?
      `;

      const fiscalResp = Array.isArray(thirdParty.fiscal_responsibilities) 
        ? thirdParty.fiscal_responsibilities.join(',') 
        : thirdParty.fiscal_responsibilities;

      const result = await window.electronAPI.dbQuery(sql, [
        thirdParty.party_type, thirdParty.person_type, thirdParty.identification_type, thirdParty.identification_number, thirdParty.check_digit,
        thirdParty.business_name, thirdParty.trade_name, thirdParty.first_name, thirdParty.middle_name, thirdParty.surname, thirdParty.second_surname,
        thirdParty.country_code, thirdParty.department_code, thirdParty.city_code, thirdParty.postal_code, thirdParty.address,
        thirdParty.tax_regime, fiscalResp, thirdParty.ciiu_code,
        thirdParty.phone, thirdParty.email, thirdParty.mobile,
        thirdParty.is_customer ? 1 : 0, thirdParty.is_supplier ? 1 : 0, 
        id
      ]);
      return result.success;
    } else {
      const response = await apiClient.put(`/accounting/third-parties/${id}/`, thirdParty);
      return response.data;
    }
  },

  async delete(id) {
    if (isDesktop()) {
      const result = await window.electronAPI.dbQuery(
        'DELETE FROM third_parties WHERE id = ?',
        [id]
      );
      return result.success;
    } else {
      await apiClient.delete(`/accounting/third-parties/${id}/`);
      return true;
    }
  }
};

/**
 * Servicio de Comprobantes
 */
export const journalEntriesService = {
  async getAll(filters = {}) {
    if (isDesktop()) {
      const result = await window.db.getJournalEntries(filters);
      return result.data || [];
    } else {
      const response = await apiClient.get('/accounting/journal-entries/', { params: filters });
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  async getById(id) {
    if (isDesktop()) {
      // Obtener comprobante con sus líneas
      const entry = await window.electronAPI.dbQuery(
        'SELECT * FROM journal_entries WHERE id = ?',
        [id]
      );
      const lines = await window.electronAPI.dbQuery(
        'SELECT * FROM journal_entry_lines WHERE journal_entry_id = ?',
        [id]
      );
      return {
        ...entry.data?.[0],
        lines: lines.data || []
      };
    } else {
      const response = await apiClient.get(`/accounting/journal-entries/${id}/`);
      return response.data;
    }
  },

  async create(entry) {
    if (isDesktop()) {
      const result = await window.db.createJournalEntry(entry);
      return result.data;
    } else {
      const response = await apiClient.post('/accounting/journal-entries/', entry);
      return response.data;
    }
  },

  async post(id) {
    if (isDesktop()) {
      const result = await window.db.postJournalEntry(id);
      return result.success;
    } else {
      const response = await apiClient.post(`/accounting/journal-entries/${id}/post/`);
      return response.data;
    }
  },

  async delete(id) {
    if (isDesktop()) {
      const result = await window.electronAPI.dbQuery(
        'DELETE FROM journal_entries WHERE id = ?',
        [id]
      );
      return result.success;
    } else {
      await apiClient.delete(`/accounting/journal-entries/${id}/`);
      return true;
    }
  }
};

/**
 * Servicio de Tipos de Documento Contable
 */
export const accountingDocumentTypesService = {
  async getAll() {
    if (isDesktop()) {
      const result = await window.db.getAccountingDocumentTypes();
      return result.data || [];
    } else {
      const response = await apiClient.get('/accounting/accounting-document-types/');
      // Handle pagination
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  }
};

/**
 * Servicio de Plantillas Contables
 */
export const accountingTemplatesService = {
  async getAll() {
    if (isDesktop()) {
      const result = await window.db.getAccountingTemplates();
      return result.data || [];
    } else {
      const response = await apiClient.get('/accounting/accounting-templates/');
      // Handle pagination
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  async getById(id) {
    if (isDesktop()) {
      const result = await window.db.getAccountingTemplateById(id);
      return result.data;
    } else {
      const response = await apiClient.get(`/accounting/accounting-templates/${id}/`);
      return response.data;
    }
  },

  async create(template) {
    if (isDesktop()) {
      const result = await window.db.createAccountingTemplate(template);
      return result.data;
    } else {
      const response = await apiClient.post('/accounting/accounting-templates/', template);
      return response.data;
    }
  },

  async update(id, template) {
    if (isDesktop()) {
      const result = await window.db.updateAccountingTemplate(id, template);
      return result.data;
    } else {
      const response = await apiClient.put(`/accounting/accounting-templates/${id}/`, template);
      return response.data;
    }
  },

  async delete(id) {
    if (isDesktop()) {
      const result = await window.db.deleteAccountingTemplate(id);
      return result.success;
    } else {
      await apiClient.delete(`/accounting/accounting-templates/${id}/`);
      return true;
    }
  }
};

/**
 * Servicio de Documentos Electrónicos DIAN
 */
export const electronicDocumentsService = {
  async getAll(filters = {}) {
    if (isDesktop()) {
      const result = await window.db.getElectronicDocuments(filters);
      return result.data || [];
    } else {
      const response = await apiClient.get('/dian/electronic-documents/', { params: filters });
      return Array.isArray(response.data) ? response.data : (response.data.results || []);
    }
  },

  async getById(id) {
    if (isDesktop()) {
      const doc = await window.electronAPI.dbQuery(
        'SELECT * FROM electronic_documents WHERE id = ?',
        [id]
      );
      const lines = await window.electronAPI.dbQuery(
        'SELECT * FROM electronic_document_lines WHERE electronic_document_id = ?',
        [id]
      );
      const taxes = await window.electronAPI.dbQuery(
        'SELECT * FROM electronic_document_taxes WHERE electronic_document_id = ?',
        [id]
      );
      return {
        ...doc.data?.[0],
        lines: lines.data || [],
        taxes: taxes.data || []
      };
    } else {
      const response = await apiClient.get(`/dian/electronic-documents/${id}/`);
      return response.data;
    }
  },

  async create(document) {
    if (isDesktop()) {
      const result = await window.db.createElectronicDocument(document);
      return result.data;
    } else {
      const response = await apiClient.post('/dian/electronic-documents/', document);
      return response.data;
    }
  },

  async send(id) {
    if (isDesktop()) {
      // En desktop, marcar para sincronización y envío
      const result = await window.electronAPI.dbQuery(
        `UPDATE electronic_documents 
         SET status = 'PENDING', needs_sync = 1 
         WHERE id = ?`,
        [id]
      );
      return result.success;
    } else {
      const response = await apiClient.post(`/dian/electronic-documents/${id}/send/`);
      return response.data;
    }
  },

  async delete(id) {
    if (isDesktop()) {
      return (await window.electronAPI.dbQuery(
        'DELETE FROM electronic_documents WHERE id = ?',
        [id]
      ));
    } else {
      const response = await apiClient.delete(`/dian/electronic-documents/${id}/`);
      return response.data;
    }
  }
};

/**
 * Servicio de Autenticación
 */
export const authService = {
  async login(credentials) {
    if (isDesktop()) {
      const result = await window.electronAPI.authLogin(credentials);
      if (result.success) {
        localStorage.setItem('user', JSON.stringify(result.user));
      }
      return result;
    } else {
      const response = await apiClient.post('/auth/login/', credentials);
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        
        // Guardar contexto del tenant
        if (response.data.client_id) {
            localStorage.setItem('client_id', response.data.client_id);
        }
      }
      return response.data;
    }
  },

  async logout() {
    if (isDesktop()) {
      await window.electronAPI.authLogout();
    }
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
  },

  async getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }
};

/**
 * Servicio de Nómina
 */
export const payrollService = {
  async getEmployees() {
    if (isDesktop()) {
        // Desktop implementation placeholder or fallback to API if hybrid
        // For now, allow direct API call if online, or throw not implemented
        const response = await apiClient.get('/payroll/employees/');
        return response.data;
    } else {
        const response = await apiClient.get('/payroll/employees/');
        return response.data;
    }
  },

  async getNoveltyTypes() {
      const response = await apiClient.get('/payroll/novelty-types/');
      return response.data;
  },

  async createNovelty(formData: FormData) {
      const response = await apiClient.post('/payroll/employee-novelties/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
  },

  async getPeriods() {
    const response = await apiClient.get('/payroll/periods/');
    return response.data;
  },

  async createPeriod(data: any) {
    const response = await apiClient.post('/payroll/periods/', data);
    return response.data;
  },

  async liquidatePeriod(id: number) {
    const response = await apiClient.post(`/payroll/periods/${id}/liquidate/`);
    return response.data;
  },

  async downloadPayslip(documentId: number) {
      const response = await apiClient.get(`/payroll/documents/${documentId}/download_payslip/`, {
          responseType: 'blob'
      });
      return response.data;
  },

  async transmitDocument(documentId: number) {
      const response = await apiClient.post(`/payroll/documents/${documentId}/transmit/`);
      return response.data;
  }
};

/**
 * Servicio de Tenant / Empresa
 */
export const tenantService = {
  async getCompanySettings() {
      // MVP: Asumimos ID 1 o endpoint 'current'
      const response = await apiClient.get('/tenants/clients/current/'); 
      // Nota: Necesitaremos crear esta acción 'current' en el viewset o usar ID 1 hardcoded
      return response.data;
  },

  async createCompany(formData: FormData) {
        const response = await apiClient.post('/tenants/clients/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        });
        return response.data;
  },

  async updateCompanySettings(id: number, formData: FormData) {
      const response = await apiClient.patch(`/tenants/clients/${id}/`, formData, {
          headers: {
              'Content-Type': 'multipart/form-data',
          }
      });
      return response.data;
  }
};

/**
 * Servicio de Sincronización (solo desktop)
 */
export const syncService = {
  async syncNow() {
    if (isDesktop()) {
      return await window.electronAPI.syncNow();
    }
    return { success: false, message: 'Solo disponible en desktop' };
  },

  async checkConnection() {
    if (isDesktop()) {
      return await window.electronAPI.checkConnection();
    }
    return { success: true, online: true };
  },

  async getStats() {
    if (isDesktop()) {
      return await window.electronAPI.getSyncStats();
    }
    return null;
  }
};

// Exportar detección de entorno
export { isDesktop };
