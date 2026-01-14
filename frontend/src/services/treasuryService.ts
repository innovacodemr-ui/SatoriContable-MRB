import { apiClient } from './api';

export interface BankAccount {
  id?: number;
  name: string;
  account_number: string;
  bank_name: string;
  currency: string;
  gl_account: number;
  gl_account_name?: string; // If returned by serializer
}

export interface PaymentOutDetail {
  id?: number;
  invoice: number; // ReceivedInvoice ID
  invoice_number?: string;
  amount_paid: number;
}

export interface PaymentOut {
  id?: number;
  consecutive?: number;
  payment_date: string;
  third_party: string; // Name of provider for now
  bank_account: number;
  bank_account_name?: string;
  payment_method: string;
  total_amount: number;
  notes: string;
  status?: 'DRAFT' | 'POSTED' | 'CANCELLED';
  details: PaymentOutDetail[];
}

const treasuryService = {
  // Bank Accounts
  getBankAccounts: async () => {
    const response = await apiClient.get('/treasury/bank-accounts/');
    return response.data;
  },

  createBankAccount: async (data: BankAccount) => {
    const response = await apiClient.post('/treasury/bank-accounts/', data);
    return response.data;
  },

  updateBankAccount: async (id: number, data: BankAccount) => {
    const response = await apiClient.put(`/treasury/bank-accounts/${id}/`, data);
    return response.data;
  },

  deleteBankAccount: async (id: number) => {
    await apiClient.delete(`/treasury/bank-accounts/${id}/`);
  },

  // Payments
  getPayments: async () => {
    const response = await apiClient.get('/treasury/payments/');
    return response.data;
  },

  createPayment: async (data: PaymentOut) => {
    const response = await apiClient.post('/treasury/payments/', data);
    return response.data;
  },

  postPayment: async (id: number) => {
    const response = await apiClient.post(`/treasury/payments/${id}/post_payment/`);
    return response.data;
  },

  // Helper to fetch pending invoices for a supplier (Needs backend support for Filtering)
  // For now fetching all received invoices
  getPendingInvoices: async (supplierId?: number) => {
    // Assuming we can filter by client or issuer_nit if we had that mapping. 
    // In MVP, we might list all and filter frontend or just list all.
    // Let's call the radian endpoint
    const response = await apiClient.get('/radian/invoices/'); 
    return response.data;
  }
};


export default treasuryService;
