import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, FileText, Users, Clock, Download, AlertCircle, CheckCircle, Plus, Search, Settings, LogOut, Eye, Filter, Check } from 'lucide-react';

// API Configuration
const API_BASE = 'http://localhost:8000/api';

// ============= TYPE DEFINITIONS =============
interface User {
  user_id: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'PROJECT_LEADER' | 'VIEWER';
  has_jira_token: boolean;
  created_at: string;
}

interface LegalClause {
  clause_id: string;
  clause_code: string;
  description: string;
  unit_price: number;
  is_active: boolean;
  created_at: string;
  created_by: string;
}

interface JiraTicket {
  ticket_id: string;
  ticket_key?: string;
  jira_key?: string;
  summary: string;
  status: string;
  time_spent_hours?: number;
  hours_worked?: number;
  assignee: string;
  is_billable: boolean;
  mapped_clause_id?: string;
  clause_id?: string;
  billable_amount?: number;
  labels: string[];
  created_at: string;
  closed_at?: string;
}

interface InvoiceLine {
  line_id: string;
  line_item_id?: string;
  jira_ticket_id: string;
  clause_id: string;
  clause_name?: string;
  description?: string;
  hours_worked?: number;
  hours?: number;
  unit_price?: number;
  rate?: number;
  line_amount?: number;
  amount?: number;
  ticket_keys?: string[];
}

interface Invoice {
  invoice_id: string;
  invoice_number?: string;
  project_name: string;
  billing_period: string;
  total_amount: number;
  total_hours?: number;
  currency?: string;
  status: 'DRAFT' | 'SENT' | 'PAID' | 'CANCELLED';
  created_at: string;
  created_by?: string;
  lines?: InvoiceLine[];
  line_items?: InvoiceLine[];
  line_count?: number;
}

type FilterBillableType = 'all' | 'billable' | 'non-billable';

// ============= SHARED COMPONENTS =============
const NavButton: React.FC<{ icon: React.ReactNode; label: string; active: boolean; onClick: () => void }> = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
      active ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
    }`}
  >
    <span className="w-5 h-5">{icon}</span>
    <span className="hidden sm:inline">{label}</span>
  </button>
);

const StatCard: React.FC<{ icon: React.ReactNode; title: string; value: string | number; subtitle: string; color: string }> = ({ icon, title, value, subtitle, color }) => (
  <div className={`${color} rounded-lg shadow-md p-6`}>
    <div className="flex items-center justify-between mb-3">
      {icon}
      <span className="text-2xl font-bold">{value}</span>
    </div>
    <h3 className="font-semibold text-gray-900">{title}</h3>
    <p className="text-sm text-gray-600 mt-1">{subtitle}</p>
  </div>
);

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const colors = {
    DRAFT: 'bg-yellow-100 text-yellow-800',
    SENT: 'bg-blue-100 text-blue-800',
    PAID: 'bg-green-100 text-green-800',
    CANCELLED: 'bg-red-100 text-red-800',
  };
  
  return (
    <span className={`px-3 py-1 text-xs font-medium rounded-full ${colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
};

const ErrorAlert: React.FC<{ error: string | null; onClose: () => void }> = ({ error, onClose }) => {
  if (!error) return null;
  
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
      <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
      <div className="flex-1">
        <h3 className="font-semibold text-red-800">Error</h3>
        <p className="text-red-700 text-sm mt-1">{error}</p>
      </div>
      <button onClick={onClose} className="text-red-600 hover:text-red-800 ml-2">×</button>
    </div>
  );
};

// ============= INVOICE GENERATOR COMPONENT =============
const InvoiceGenerator: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({ onClose, onSuccess }) => {
  const [step, setStep] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [projectName, setProjectName] = useState<string>('BMW FLASH Project');
  const [jiraProjectKey, setJiraProjectKey] = useState<string>('BMW');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  
  const [availableTickets, setAvailableTickets] = useState<JiraTicket[]>([]);
  const [selectedTickets, setSelectedTickets] = useState<Set<string>>(new Set());
  const [filterBillable, setFilterBillable] = useState<FilterBillableType>('all');
  
  const [generatedInvoice, setGeneratedInvoice] = useState<Invoice | null>(null);

  useEffect(() => {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    setStartDate(firstDay.toISOString().split('T')[0]);
    setEndDate(lastDay.toISOString().split('T')[0]);
  }, []);

  const fetchTickets = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/jira/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_key: jiraProjectKey,
          billing_period_start: `${startDate}T00:00:00Z`,
          billing_period_end: `${endDate}T23:59:59Z`,
          status_filter: 'CLOSED'
        })
      });

      if (!response.ok) throw new Error(`Failed to fetch tickets: ${response.statusText}`);
      
      const data = await response.json();
      console.log(data)
      const tickets: JiraTicket[] = data.tickets || [];
      setAvailableTickets(tickets);
      
      const billableIds = new Set<string>(
        tickets.filter((t: JiraTicket) => t.is_billable).map((t: JiraTicket) => t.ticket_id)
      );
      setSelectedTickets(billableIds);
      
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const generateInvoice = async (): Promise<void> => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/invoices/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: projectName,
          billing_period: startDate.substring(0, 7),
          jira_project_key: jiraProjectKey,
          billing_period_start: `${startDate}T00:00:00Z`,
          billing_period_end: `${endDate}T23:59:59Z`,
          selected_tickets: Array.from(selectedTickets)
        })
      });

      if (!response.ok) throw new Error(`Failed to generate invoice: ${response.statusText}`);
      
      const invoice: Invoice = await response.json();
      setGeneratedInvoice(invoice);
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const toggleTicket = (ticketId: string): void => {
    const newSelection = new Set(selectedTickets);
    if (newSelection.has(ticketId)) {
      newSelection.delete(ticketId);
    } else {
      newSelection.add(ticketId);
    }
    setSelectedTickets(newSelection);
  };

  const toggleAll = (): void => {
    const filteredIds = getFilteredTickets().map((t: JiraTicket) => t.ticket_id);
    const allSelected = filteredIds.every((id: string) => selectedTickets.has(id));
    
    const newSelection = new Set(selectedTickets);
    if (allSelected) {
      filteredIds.forEach((id: string) => newSelection.delete(id));
    } else {
      filteredIds.forEach((id: string) => newSelection.add(id));
    }
    setSelectedTickets(newSelection);
  };

  const getFilteredTickets = (): JiraTicket[] => {
    if (filterBillable === 'all') return availableTickets;
    if (filterBillable === 'billable') return availableTickets.filter((t: JiraTicket) => t.is_billable);
    return availableTickets.filter((t: JiraTicket) => !t.is_billable);
  };

  const calculateTotals = (): { totalHours: number; totalAmount: number; ticketCount: number } => {
    const selected = availableTickets.filter((t: JiraTicket) => selectedTickets.has(t.ticket_id));
    const totalHours = selected.reduce((sum: number, t: JiraTicket) => sum + (Number(t.time_spent_hours || t.hours_worked) || 0), 0);
    const totalAmount = selected.reduce((sum: number, t: JiraTicket) => sum + (Number(t.billable_amount) || 0), 0);
    return { totalHours, totalAmount, ticketCount: selected.length };
  };

  const totals = calculateTotals();
  const filteredTickets = getFilteredTickets();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
      <div className="bg-white rounded-lg shadow-2xl max-w-6xl w-full my-8">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-t-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">Invoice Generator</h2>
              <p className="text-blue-100 mt-1">Generate invoices from Jira tickets</p>
            </div>
            <button onClick={onClose} className="text-white hover:bg-white/20 rounded-lg p-2 transition-colors">
              <span className="text-2xl">×</span>
            </button>
          </div>
          
          {/* Progress Steps */}
          <div className="flex items-center justify-between mt-6">
            <div className={`flex items-center ${step >= 1 ? 'text-white' : 'text-blue-300'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 1 ? 'bg-white text-blue-600' : 'bg-blue-500'}`}>
                1
              </div>
              <span className="ml-2 font-medium">Period</span>
            </div>
            <div className="flex-1 h-1 mx-4 bg-blue-500">
              <div className={`h-full ${step >= 2 ? 'bg-white' : 'bg-blue-500'} transition-all`} />
            </div>
            <div className={`flex items-center ${step >= 2 ? 'text-white' : 'text-blue-300'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 2 ? 'bg-white text-blue-600' : 'bg-blue-500'}`}>
                2
              </div>
              <span className="ml-2 font-medium">Tickets</span>
            </div>
            <div className="flex-1 h-1 mx-4 bg-blue-500">
              <div className={`h-full ${step >= 3 ? 'bg-white' : 'bg-blue-500'} transition-all`} />
            </div>
            <div className={`flex items-center ${step >= 3 ? 'text-white' : 'text-blue-300'}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step >= 3 ? 'bg-white text-blue-600' : 'bg-blue-500'}`}>
                3
              </div>
              <span className="ml-2 font-medium">Review</span>
            </div>
          </div>
        </div>

        <div className="p-6 max-h-[calc(100vh-16rem)] overflow-y-auto">
          <ErrorAlert error={error} onClose={() => setError(null)} />

          {/* Step 1: Select Period */}
          {step === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Project Name</label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Jira Project Key</label>
                <input
                  type="text"
                  value={jiraProjectKey}
                  onChange={(e) => setJiraProjectKey(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="e.g., BMW"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
              
              <button
                onClick={fetchTickets}
                disabled={loading || !startDate || !endDate}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Fetching Tickets...' : 'Continue to Ticket Selection'}
              </button>
            </div>
          )}

          {/* Step 2: Select Tickets */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-800">Select Tickets to Include</h3>
                <button onClick={() => setStep(1)} className="text-blue-600 hover:text-blue-800 font-medium">
                  ← Back
                </button>
              </div>
              
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <Filter className="w-5 h-5 text-gray-600" />
                  <select
                    value={filterBillable}
                    onChange={(e) => setFilterBillable(e.target.value as FilterBillableType)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Tickets ({availableTickets.length})</option>
                    <option value="billable">Billable ({availableTickets.filter(t => t.is_billable).length})</option>
                    <option value="non-billable">Non-Billable ({availableTickets.filter(t => !t.is_billable).length})</option>
                  </select>
                </div>
                
                <button onClick={toggleAll} className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 font-medium">
                  {filteredTickets.every(t => selectedTickets.has(t.ticket_id)) ? 'Deselect All' : 'Select All'}
                </button>
              </div>
              
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-sm text-blue-600 font-medium">Selected</div>
                  <div className="text-2xl font-bold text-blue-900">{totals.ticketCount}</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-sm text-green-600 font-medium">Hours</div>
                  <div className="text-2xl font-bold text-green-900">{totals.totalHours.toFixed(2)}</div>
                </div>
                <div className="bg-purple-50 p-4 rounded-lg">
                  <div className="text-sm text-purple-600 font-medium">Amount</div>
                  <div className="text-2xl font-bold text-purple-900">€{totals.totalAmount.toFixed(2)}</div>
                </div>
              </div>
              
              <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
                {filteredTickets.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">No tickets found</div>
                ) : (
                  filteredTickets.map((ticket: JiraTicket) => (
                    <div
                      key={ticket.ticket_id}
                      onClick={() => toggleTicket(ticket.ticket_id)}
                      className={`p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedTickets.has(ticket.ticket_id) ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-start">
                        <input
                          type="checkbox"
                          checked={selectedTickets.has(ticket.ticket_id)}
                          onChange={() => {}}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded mt-1 mr-3"
                        />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-2">
                              <span className="font-semibold text-gray-900">{ticket.ticket_key || ticket.jira_key}</span>
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                ticket.is_billable ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                              }`}>
                                {ticket.is_billable ? 'Billable' : 'Non-Billable'}
                              </span>
                            </div>
                            <div className="text-right">
                              <div className="text-sm font-semibold text-gray-900">
                                €{Number(ticket.billable_amount || 0).toFixed(2)}
                              </div>
                              <div className="text-xs text-gray-500">
                                {(Number(ticket.time_spent_hours || ticket.hours_worked) || 0).toFixed(2)}h
                              </div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-700 mt-1">{ticket.summary}</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
              
              <button
                onClick={generateInvoice}
                disabled={loading || selectedTickets.size === 0}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Generating...' : `Generate Invoice (${selectedTickets.size} tickets)`}
              </button>
            </div>
          )}

          {/* Step 3: Review Invoice */}
          {step === 3 && generatedInvoice && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-800">Invoice Generated</h3>
                <button onClick={() => setStep(2)} className="text-blue-600 hover:text-blue-800 font-medium">
                  ← Back
                </button>
              </div>
              
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center">
                  <CheckCircle className="w-6 h-6 text-green-600 mr-3" />
                  <div>
                    <h4 className="font-semibold text-green-800">Success!</h4>
                    <p className="text-sm text-green-700">Invoice {generatedInvoice.invoice_id} created</p>
                  </div>
                </div>
              </div>
              
              <div className="border border-gray-200 rounded-lg p-6">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-3">Details</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Number:</span>
                        <span className="font-medium">{generatedInvoice.invoice_number || generatedInvoice.invoice_id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Project:</span>
                        <span className="font-medium">{generatedInvoice.project_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Period:</span>
                        <span className="font-medium">{generatedInvoice.billing_period}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-gray-700 mb-3">Summary</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Hours:</span>
                        <span className="font-medium">{generatedInvoice.total_hours?.toFixed(2) || '0.00'}</span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-gray-200">
                        <span className="font-semibold text-gray-800">Total:</span>
                        <span className="font-bold text-lg text-blue-600">
                          €{Number(generatedInvoice.total_amount).toFixed(2)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex space-x-4">
                <button className="flex-1 bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center justify-center">
                  <Download className="w-5 h-5 mr-2" />
                  Download PDF
                </button>
                <button 
                  onClick={() => {
                    onSuccess();
                    onClose();
                  }}
                  className="flex-1 bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
                >
                  Done
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ============= MAIN APP COMPONENT =============
const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'clauses' | 'tickets' | 'invoices' | 'settings'>('dashboard');
  const [showInvoiceGenerator, setShowInvoiceGenerator] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [clauses, setClauses] = useState<LegalClause[]>([]);
  const [tickets, setTickets] = useState<JiraTicket[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCurrentUser();
  }, []);

  useEffect(() => {
    if (!currentUser) return;
    
    switch (currentView) {
      case 'clauses':
        fetchClauses();
        break;
      case 'tickets':
        fetchTickets();
        break;
      case 'invoices':
        fetchInvoices();
        break;
      case 'dashboard':
        fetchClauses();
        fetchTickets();
        fetchInvoices();
        break;
    }
  }, [currentView, currentUser]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_BASE}/users/me`);
      if (!response.ok) throw new Error('Failed to fetch user');
      const data = await response.json();
      setCurrentUser(data);
    } catch (err) {
      setError('Failed to load user information');
    }
  };

  const fetchClauses = async () => {
    try {
      const response = await fetch(`${API_BASE}/clauses?active_only=true`);
      if (!response.ok) throw new Error('Failed to fetch clauses');
      const data = await response.json();
      setClauses(data);
    } catch (err) {
      setError('Failed to load clauses');
    }
  };

  const fetchTickets = async () => {
    try {
      const response = await fetch(`${API_BASE}/jira/tickets`);
      if (!response.ok) throw new Error('Failed to fetch tickets');
      const data = await response.json();
      setTickets(data);
    } catch (err) {
      setError('Failed to load tickets');
    }
  };

  const fetchInvoices = async () => {
    try {
      const response = await fetch(`${API_BASE}/invoices`);
      if (!response.ok) throw new Error('Failed to fetch invoices');
      const data = await response.json();
      setInvoices(data);
    } catch (err) {
      setError('Failed to load invoices');
    }
  };

  const updateJiraToken = async (token: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/users/jira-token`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update token');
      }
      
      alert('Jira token updated successfully!');
      await fetchCurrentUser();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading application...</p>
        </div>
      </div>
    );
  }

  const DashboardView = () => {
    const totalBillableHours = tickets.filter(t => t.is_billable).reduce((sum, t) => sum + (Number(t.hours_worked || t.time_spent_hours) || 0), 0);
    const totalRevenue = invoices.reduce((sum, inv) => sum + (Number(inv.total_amount) || 0), 0);
    const pendingInvoices = invoices.filter(inv => inv.status === 'DRAFT').length;

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={<Clock className="w-8 h-8 text-blue-600" />}
            title="Billable Hours"
            value={totalBillableHours.toFixed(1)}
            subtitle="This month"
            color="bg-blue-50"
          />
          <StatCard
            icon={<DollarSign className="w-8 h-8 text-green-600" />}
            title="Total Revenue"
            value={`€${totalRevenue.toLocaleString()}`}
            subtitle="All invoices"
            color="bg-green-50"
          />
          <StatCard
            icon={<FileText className="w-8 h-8 text-purple-600" />}
            title="Pending Invoices"
            value={pendingInvoices}
            subtitle="Awaiting approval"
            color="bg-purple-50"
          />
          <StatCard
            icon={<Users className="w-8 h-8 text-orange-600" />}
            title="Active Clauses"
            value={clauses.filter(c => c.is_active).length}
            subtitle="Legal clauses"
            color="bg-orange-50"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Recent Invoices
            </h3>
            <div className="space-y-3">
              {invoices.slice(0, 3).map(invoice => (
                <div key={invoice.invoice_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                  <div>
                    <p className="font-medium">{invoice.invoice_number || invoice.invoice_id}</p>
                    <p className="text-sm text-gray-600">{invoice.billing_period}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-green-600">€{invoice.total_amount.toLocaleString()}</p>
                    <StatusBadge status={invoice.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Recent Tickets
            </h3>
            <div className="space-y-3">
              {tickets.slice(0, 3).map(ticket => (
                <div key={ticket.ticket_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                  <div>
                    <p className="font-medium">{ticket.ticket_key || ticket.jira_key}</p>
                    <p className="text-sm text-gray-600">{ticket.summary}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{(Number(ticket.hours_worked || ticket.time_spent_hours) || 0).toFixed(1)}h</p>
                    {ticket.is_billable && <span className="text-xs text-green-600">Billable</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-blue-600 to-blue-700 rounded-lg shadow-md p-6 text-white">
          <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button 
              onClick={() => setShowInvoiceGenerator(true)} 
              disabled={loading || !currentUser.has_jira_token} 
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              Generate Invoice
            </button>
            <button 
              onClick={() => setCurrentView('invoices')} 
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-6 py-3 rounded-lg font-medium transition-colors"
            >
              View All Invoices
            </button>
            <button 
              onClick={() => setCurrentView('tickets')} 
              className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-6 py-3 rounded-lg font-medium transition-colors"
            >
              View Tickets
            </button>
          </div>
          {!currentUser.has_jira_token && (
            <p className="mt-4 text-yellow-200 text-sm">⚠️ Please configure your Jira token in Settings to generate invoices</p>
          )}
        </div>
      </div>
    );
  };

  const ClausesView = () => {
    const filteredClauses = clauses.filter(c =>
      (c.clause_code || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.description || '').toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold">Legal Clauses</h2>
          {currentUser.role === 'ADMIN' && (
            <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
              <Plus className="w-4 h-4" />
              Add Clause
            </button>
          )}
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search clauses..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredClauses.map(clause => (
            <div key={clause.clause_id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold text-blue-600">{clause.clause_code}</h3>
                  <p className="text-gray-600 mt-1">{clause.description}</p>
                </div>
                {clause.is_active && (
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">Active</span>
                )}
              </div>
              <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200">
                <span className="text-2xl font-bold text-green-600">€{Number(clause.unit_price || 0).toFixed(2)}/h</span>
                {currentUser.role === 'ADMIN' && (
                  <button className="text-blue-600 hover:text-blue-700 font-medium">Edit</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const TicketsView = () => {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold">Jira Tickets</h2>
          <button 
            onClick={() => setShowInvoiceGenerator(true)} 
            disabled={loading || !currentUser.has_jira_token} 
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Generate Invoice
          </button>
        </div>

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ticket</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Summary</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assignee</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hours</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Billable</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {tickets.map(ticket => (
                  <tr key={ticket.ticket_id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium text-blue-600">{ticket.ticket_key || ticket.jira_key}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-900">{ticket.summary}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-gray-600">{ticket.assignee}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium">{(Number(ticket.hours_worked || ticket.time_spent_hours) || 0).toFixed(1)}h</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">{ticket.status}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {ticket.is_billable ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-gray-400" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const InvoicesView = () => {
    return (
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <h2 className="text-2xl font-bold">Invoices</h2>
          <button 
            onClick={() => setShowInvoiceGenerator(true)} 
            disabled={loading} 
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Generate Invoice
          </button>
        </div>

        <div className="space-y-4">
          {invoices.map(invoice => (
            <div key={invoice.invoice_id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-blue-600">{invoice.invoice_number || invoice.invoice_id}</h3>
                  <p className="text-gray-600 mt-1">{invoice.project_name} - {invoice.billing_period}</p>
                  <p className="text-sm text-gray-500 mt-1">Generated: {new Date(invoice.created_at).toLocaleDateString()}</p>
                  <p className="text-sm text-gray-500">Line items: {invoice.line_count || 0}</p>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Total Amount</p>
                    <p className="text-2xl font-bold text-green-600">€{invoice.total_amount.toLocaleString()}</p>
                  </div>
                  <StatusBadge status={invoice.status} />
                </div>
              </div>

              <div className="flex gap-3 mt-4 pt-4 border-t border-gray-200">
                <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                  <Eye className="w-4 h-4" />
                  View Details
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
                  <Download className="w-4 h-4" />
                  Export PDF
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const SettingsView = () => {
    const [jiraToken, setJiraToken] = useState('');

    const handleUpdateToken = () => {
      if (!jiraToken.trim()) {
        alert('Please enter a Jira token');
        return;
      }
      updateJiraToken(jiraToken);
      setJiraToken('');
    };

    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold">Settings</h2>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">User Profile</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input type="text" value={currentUser.name} readOnly className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={currentUser.email} readOnly className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
              <input type="text" value={currentUser.role} readOnly className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-4">Jira Integration</h3>
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2">
              <label className="block text-sm font-medium text-gray-700">Jira Personal Access Token</label>
              {currentUser.has_jira_token && (
                <CheckCircle className="w-5 h-5 text-green-600" />
              )}
            </div>
            <input 
              type="password" 
              placeholder="Enter your Jira PAT" 
              value={jiraToken}
              onChange={(e) => setJiraToken(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
            />
            <button 
              onClick={handleUpdateToken}
              disabled={loading}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              Update Token
            </button>
            {currentUser.has_jira_token && (
              <p className="text-sm text-green-600">✓ Jira token is configured</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Legal Billing System</h1>
                <p className="text-sm text-gray-600">BMW FLASH Project</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right hidden sm:block">
                <p className="font-medium text-gray-900">{currentUser.name}</p>
                <p className="text-sm text-gray-600">{currentUser.role}</p>
              </div>
              <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <LogOut className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Display */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <ErrorAlert error={error} onClose={() => setError(null)} />
        </div>
      )}

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-1 overflow-x-auto">
            <NavButton icon={<FileText />} label="Dashboard" active={currentView === 'dashboard'} onClick={() => setCurrentView('dashboard')} />
            <NavButton icon={<DollarSign />} label="Clauses" active={currentView === 'clauses'} onClick={() => setCurrentView('clauses')} />
            <NavButton icon={<Clock />} label="Tickets" active={currentView === 'tickets'} onClick={() => setCurrentView('tickets')} />
            <NavButton icon={<Calendar />} label="Invoices" active={currentView === 'invoices'} onClick={() => setCurrentView('invoices')} />
            <NavButton icon={<Settings />} label="Settings" active={currentView === 'settings'} onClick={() => setCurrentView('settings')} />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 flex items-center gap-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="font-medium">Processing...</p>
            </div>
          </div>
        )}
        
        {currentView === 'dashboard' && <DashboardView />}
        {currentView === 'clauses' && <ClausesView />}
        {currentView === 'tickets' && <TicketsView />}
        {currentView === 'invoices' && <InvoicesView />}
        {currentView === 'settings' && <SettingsView />}
      </main>

      {/* Invoice Generator Modal */}
      {showInvoiceGenerator && (
        <InvoiceGenerator 
          onClose={() => setShowInvoiceGenerator(false)} 
          onSuccess={() => {
            fetchInvoices();
            fetchTickets();
          }} 
        />
      )}
    </div>
  );
};

export default App;