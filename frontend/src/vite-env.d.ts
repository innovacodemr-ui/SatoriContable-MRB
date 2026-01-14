/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Tipos para Electron API
interface ElectronAPI {
  isDesktop: boolean;
  invoke: (channel: string, ...args: any[]) => Promise<any>;
  getConfig: () => Promise<any>;
  setConfig: (config: any) => Promise<any>;
  dbQuery: (sql: string, params?: any[]) => Promise<{ success: boolean; data?: any; error?: string }>;
  dbTransaction: (queries: any[]) => Promise<{ success: boolean; data?: any; error?: string }>;
  syncNow: () => Promise<any>;
  checkConnection: () => Promise<any>;
  getSyncStats: () => Promise<any>;
  authLogin: (credentials: any) => Promise<any>;
  authLogout: () => Promise<any>;
  loadPUC: () => Promise<{ success: boolean; inserted?: number; skipped?: number; errors?: number; total?: number; error?: string }>;
  loadTestData: () => Promise<{ success: boolean; thirdParties?: number; journalEntries?: number; documents?: number; error?: string }>;
  onSyncStart: (callback: () => void) => void;
  onSyncComplete: (callback: (data: any) => void) => void;
  onSyncError: (callback: (error: string) => void) => void;
  onConnectionChange: (callback: (data: any) => void) => void;
}

interface Window {
  electronAPI?: ElectronAPI;
  db?: any;
}

interface DatabaseAPI {
  getAccounts: (filters?: any) => Promise<{ success: boolean; data?: any }>;
  createAccount: (account: any) => Promise<{ success: boolean; data?: any }>;
  updateAccount: (id: number, account: any) => Promise<{ success: boolean; data?: any }>;
  getJournalEntries: (filters?: any) => Promise<{ success: boolean; data?: any }>;
  createJournalEntry: (entry: any) => Promise<{ success: boolean; data?: any }>;
  postJournalEntry: (id: number) => Promise<{ success: boolean; data?: any }>;
  getThirdParties: (filters?: any) => Promise<{ success: boolean; data?: any }>;
  createThirdParty: (thirdParty: any) => Promise<{ success: boolean; data?: any }>;
  getElectronicDocuments: (filters?: any) => Promise<{ success: boolean; data?: any }>;
  createElectronicDocument: (document: any) => Promise<{ success: boolean; data?: any }>;
}

interface Window {
  electronAPI?: ElectronAPI;
  db?: DatabaseAPI;
}
