// Base API config (similar to api.ts, reusing the instance if possible, but for now independent for speed or importing api.ts)
// Ideally we should import the configured client from './api'
import { apiClient } from './api';

export interface SupportDocument {
  id?: number;
  consecutive?: string;
  issue_date: string;
  due_date: string;
  supplier: number; // ID of ThirdParty/Supplier
  supplier_name?: string; // Display name
  items: SupportDocumentItem[];
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  status?: 'DRAFT' | 'SENT_DIAN';
  resolution?: number; // Optional, might be auto-selected by backend
}

export interface SupportDocumentItem {
  id?: number;
  description: string;
  quantity: number;
  unit_price: number;
  total_amount: number; // calculated
}

export interface Supplier {
  id: number;
  name: string; // trade_name or legal_name
  identification_number: string;
}

const purchasesService = {
  // Support Documents
  getSupportDocuments: async () => {
    const response = await apiClient.get('/support-docs/documents/');
    return response.data;
  },

  getSupportDocument: async (id: number) => {
    const response = await apiClient.get(`/support-docs/documents/${id}/`);
    return response.data;
  },

  createSupportDocument: async (data: SupportDocument) => {
    const response = await apiClient.post('/support-docs/documents/', data);
    return response.data;
  },

  transmitToDian: async (id: number) => {
    const response = await apiClient.post(`/support-docs/documents/${id}/transmit/`);
    return response.data;
  },

  // Suppliers (Using ThirdParties endpoint for now as /api/suppliers/ doesn't exist yet)
  // Assuming Backend has this data in accounting/third-parties
  getSuppliers: async (search?: string) => {
    const params = search ? { search } : {};
    const response = await apiClient.get('/accounting/third-parties/', { params });
    // If backend doesn't filter by 'is_supplier' we might get clients too, but for MVP this works.
    return response.data;
  }
};

export default purchasesService;
