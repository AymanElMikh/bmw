import React, { useState, useEffect } from 'react';
import { Calendar, DollarSign, FileText, Users, Clock, Download, AlertCircle, CheckCircle, Plus, Search, Filter, Settings, LogOut, Eye } from 'lucide-react';

// API Configuration
const API_BASE = 'http://localhost:8000/api';

// Types matching FastAPI backend
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
  jira_key: string;
  summary: string;
  status: string;
  hours_worked: number;
  assignee: string;
  is_billable: boolean;
  clause_id?: string;
  labels: string[];
  created_at: string;
  closed_at?: string;
}

interface InvoiceLine {
  line_id: string;
  jira_ticket_id: string;
  clause_id: string;
  hours_worked: number;
  unit_price: number;
  line_amount: number;
}

interface Invoice {
  invoice_id: string;
  project_name: string;
  billing_period: string;
  total_amount: number;
  currency: string;
  status: 'DRAFT' | 'SENT' | 'PAID' | 'CANCELLED';
  created_at: string;
  created_by: string;
  lines: InvoiceLine[];
}

interface InvoiceListItem {
  invoice_id: string;
  project_name: string;
  billing_period: string;
  total_amount: number;
  status: string;
  created_at: string;
  line_count: number;
}

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<'dashboard' | 'clauses' | 'tickets' | 'invoices' | 'settings'>('dashboard');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [clauses, setClauses] = useState<LegalClause[]>([]);
  const [tickets, setTickets] = useState<JiraTicket[]>([]);
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch current user on mount
  useEffect(() => {
    fetchCurrentUser();
  }, []);

  // Fetch data when view changes
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
      console.error(err);
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
      console.error(err);
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
      console.error(err);
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
      console.error(err);
    }
  };

  const fetchJiraTickets = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/jira/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          end_date: new Date().toISOString(),
          status_filter: 'CLOSED'
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch Jira tickets');
      }
      
      const data = await response.json();
      alert(`Fetched ${data.billable_count} billable tickets out of ${data.total_count} total`);
      await fetchTickets();
    } catch (err: any) {
      setError(err.message);
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const generateInvoice = async () => {
    setLoading(true);
    setError(null);
    try {
      const currentMonth = new Date().toISOString().slice(0, 7);
      const response = await fetch(`${API_BASE}/invoices/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: 'BMW FLASH Project',
          billing_period: currentMonth
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate invoice');
      }
      
      const data = await response.json();
      alert(`Invoice ${data.invoice_id} generated successfully! Total: €${data.total_amount.toLocaleString()}`);
      await fetchInvoices();
    } catch (err: any) {
      setError(err.message);
      alert(err.message);
    } finally {
      setLoading(false);
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
      alert(err.message);
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
    const totalBillableHours = tickets.filter(t => t.is_billable).reduce((sum, t) => sum + (Number(t.hours_worked) || 0), 0);
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
                    <p className="font-medium">{invoice.invoice_id}</p>
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
                    <p className="font-medium">{ticket.jira_key}</p>
                    <p className="text-sm text-gray-600">{ticket.summary}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{ticket.hours_worked}h</p>
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
            <button onClick={fetchJiraTickets} disabled={loading || !currentUser.has_jira_token} className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50">
              Fetch Jira Tickets
            </button>
            <button onClick={generateInvoice} disabled={loading} className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50">
              Generate Invoice
            </button>
            <button onClick={() => setCurrentView('invoices')} className="bg-white/10 hover:bg-white/20 backdrop-blur-sm px-6 py-3 rounded-lg font-medium transition-colors">
              View All Invoices
            </button>
          </div>
          {!currentUser.has_jira_token && (
            <p className="mt-4 text-yellow-200 text-sm">⚠️ Please configure your Jira token in Settings to fetch tickets</p>
          )}
        </div>
      </div>
    );
  };

  const ClausesView = () => {
    const filteredClauses = clauses.filter(c => 
      c.clause_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.description.toLowerCase().includes(searchTerm.toLowerCase())
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
                <span className="text-2xl font-bold text-green-600">€{clause.unit_price.toFixed(2)}/h</span>
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
          <button onClick={fetchJiraTickets} disabled={loading || !currentUser.has_jira_token} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
            <Download className="w-4 h-4" />
            Fetch Tickets
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
                      <span className="font-medium text-blue-600">{ticket.jira_key}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-gray-900">{ticket.summary}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-gray-600">{ticket.assignee}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium">{ticket.hours_worked}h</span>
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
          <button onClick={generateInvoice} disabled={loading} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50">
            <Plus className="w-4 h-4" />
            Generate Invoice
          </button>
        </div>

        <div className="space-y-4">
          {invoices.map(invoice => (
            <div key={invoice.invoice_id} className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-blue-600">{invoice.invoice_id}</h3>
                  <p className="text-gray-600 mt-1">{invoice.project_name} - {invoice.billing_period}</p>
                  <p className="text-sm text-gray-500 mt-1">Generated: {new Date(invoice.created_at).toLocaleDateString()}</p>
                  <p className="text-sm text-gray-500">Line items: {invoice.line_count}</p>
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
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <p className="text-red-800">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-red-600 hover:text-red-800">×</button>
          </div>
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
    </div>
  );
};

const NavButton: React.FC<{ icon: React.ReactNode; label: string; active: boolean; onClick: () => void }> = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}className={`flex items-center gap-2 px-4 py-3 font-medium transition-colors whitespace-nowrap ${
      active
        ? 'text-blue-600 border-b-2 border-blue-600'
        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
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

export default App;