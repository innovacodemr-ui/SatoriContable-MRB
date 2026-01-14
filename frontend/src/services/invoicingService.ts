import { apiClient, isDesktop } from './api';

export interface Resolution {
  id?: number;
  name: string;
  doc_type: 'INVOICE' | 'SUPPORT_DOC';
  prefix: string;
  number: string;
  start_range: number;
  end_range: number;
  current_number: number;
  start_date: string;
  end_date: string;
  technical_key: string;
  is_active: boolean;
}

const getResolutions = async () => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('get-resolutions'));
    }
    const response = await apiClient.get('/invoicing/resolutions/');
    return response.data;
};

const createResolution = async (resolution: Resolution) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('create-resolution', resolution));
    }
    const response = await apiClient.post('/invoicing/resolutions/', resolution);
    return response.data;
};

const updateResolution = async (id: number, resolution: Resolution) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('update-resolution', { id, ...resolution }));
    }
    const response = await apiClient.put(`/invoicing/resolutions/${id}/`, resolution);
    return response.data;
};

const deleteResolution = async (id: number) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('delete-resolution', id));
    }
    const response = await apiClient.delete(`/invoicing/resolutions/${id}/`);
    return response.data;
};

// --- Invoices ---

export interface InvoiceLine {
    item?: number; // Item ID
    description: string;
    quantity: number;
    unit_price: number;
    tax_rate: number;
    subtotal?: number;
    tax_amount?: number;
    total?: number;
}

export interface Invoice {
    id?: number;
    resolution: number;
    customer: number;
    customer_name?: string;
    prefix?: string;
    number?: number;
    payment_due_date: string;
    payment_term: string;
    notes?: string;
    lines: InvoiceLine[];
    subtotal?: number;
    tax_total?: number;
    total?: number;
    status?: string;
}

const createInvoice = async (invoice: Invoice) => {
    if (isDesktop()) {
        return (await window.electronAPI!.invoke('create-invoice', invoice));
    }
    const response = await apiClient.post('/invoicing/invoices/', invoice);
    return response.data;
};

const getInvoices = async () => {
     if (isDesktop()) {
        return (await window.electronAPI!.invoke('get-invoices'));
    }
    const response = await apiClient.get('/invoicing/invoices/');
    return response.data;
};

const deleteInvoice = async (id: any) => {
    if (isDesktop()) {
       // return (await window.electronAPI!.invoke('delete-invoice', id));
       return; 
    }
    const response = await apiClient.delete(`/invoicing/invoices/${id}/`);
    return response.data;
};


const invoicingService = {
    getResolutions,
    createResolution,
    updateResolution,
    deleteResolution,
    createInvoice,
    getInvoices,
    delete: deleteInvoice
};

export default invoicingService;
