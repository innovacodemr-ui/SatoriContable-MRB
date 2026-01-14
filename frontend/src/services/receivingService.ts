import { apiClient } from './api';

export const receivingService = {
    // Subir XML
    uploadInvoice: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await apiClient.post('/radian/receive/upload/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    // Listar Facturas
    listInvoices: async () => {
        const response = await apiClient.get('/radian/receive/list/');
        return response.data;
    },

    // Enviar Evento (030, 032, etc)
    sendEvent: async (invoiceId: number, eventCode: string = '030') => {
        const response = await apiClient.post(`/radian/send-event/${invoiceId}/`, {
            event_code: eventCode
        });
        return response.data;    },

    async syncEmail() {
        const response = await apiClient.post('/radian/receive/sync-email/');
        return response.data;    
    },

    // Contabilizar Factura
    postToAccounting: async (invoiceId: number, templateId: number) => {
        const response = await apiClient.post(`/radian/invoices/${invoiceId}/post_to_accounting/`, {
            template_id: templateId
        });
        return response.data;
    }
};
