import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { expensesApi, revenueApi, invoicesApi } from '../../services/api';

export function FinancialPage() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState({
    totalRevenue: 0,
    totalExpenses: 0,
    netIncome: 0,
    profitMargin: 0,
  });
  const [recentExpenses, setRecentExpenses] = useState<any[]>([]);
  const [recentRevenue, setRecentRevenue] = useState<any[]>([]);
  const [recentInvoices, setRecentInvoices] = useState<any[]>([]);

  useEffect(() => {
    loadFinancialData();
  }, []);

  const loadFinancialData = async () => {
    try {
      // Get current month dates
      const now = new Date();
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
      const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);

      const startDate = firstDay.toISOString().split('T')[0];
      const endDate = lastDay.toISOString().split('T')[0];

      const [expensesData, revenueData, invoicesData] = await Promise.all([
        expensesApi.list({ start_date: startDate, end_date: endDate, limit: 10 }),
        revenueApi.list({ start_date: startDate, end_date: endDate, limit: 10 }),
        invoicesApi.list({ limit: 10 }),
      ]);

      // Calculate summary
      const totalRevenue = revenueData.summary?.total_amount || 0;
      const totalExpenses = expensesData.summary?.total_amount || 0;
      const netIncome = totalRevenue - totalExpenses;
      const profitMargin = totalRevenue > 0 ? (netIncome / totalRevenue) * 100 : 0;

      setSummary({
        totalRevenue,
        totalExpenses,
        netIncome,
        profitMargin,
      });

      setRecentExpenses(expensesData.expenses || []);
      setRecentRevenue(revenueData.revenue || []);
      setRecentInvoices(invoicesData.invoices || []);
    } catch (error) {
      console.error('Failed to load financial data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Financial Dashboard</h1>
        <div className="text-sm text-gray-600">
          Current Month: {new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <h3 className="text-sm font-medium text-green-800 mb-2">Total Revenue</h3>
          <p className="text-3xl font-bold text-green-900">
            ${summary.totalRevenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-green-700 mt-2">Current month</p>
        </div>

        <div className="card bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <h3 className="text-sm font-medium text-red-800 mb-2">Total Expenses</h3>
          <p className="text-3xl font-bold text-red-900">
            ${summary.totalExpenses.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-red-700 mt-2">Current month</p>
        </div>

        <div className={`card ${summary.netIncome >= 0 ? 'bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200' : 'bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200'}`}>
          <h3 className={`text-sm font-medium mb-2 ${summary.netIncome >= 0 ? 'text-blue-800' : 'text-orange-800'}`}>
            Net Income
          </h3>
          <p className={`text-3xl font-bold ${summary.netIncome >= 0 ? 'text-blue-900' : 'text-orange-900'}`}>
            ${Math.abs(summary.netIncome).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className={`text-xs mt-2 ${summary.netIncome >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
            {summary.netIncome >= 0 ? 'Profit' : 'Loss'}
          </p>
        </div>

        <div className="card bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <h3 className="text-sm font-medium text-purple-800 mb-2">Profit Margin</h3>
          <p className="text-3xl font-bold text-purple-900">
            {summary.profitMargin.toFixed(1)}%
          </p>
          <p className="text-xs text-purple-700 mt-2">
            {summary.profitMargin > 20 ? 'Excellent' : summary.profitMargin > 10 ? 'Good' : 'Needs improvement'}
          </p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/app/financial/expenses"
            className="card hover:shadow-md transition-shadow bg-gray-50 hover:bg-gray-100"
          >
            <span className="text-2xl mb-2 block">💸</span>
            <h3 className="font-medium text-gray-900">Manage Expenses</h3>
            <p className="text-sm text-gray-600 mt-1">View and add expenses</p>
          </Link>

          <Link
            to="/app/financial/revenue"
            className="card hover:shadow-md transition-shadow bg-gray-50 hover:bg-gray-100"
          >
            <span className="text-2xl mb-2 block">💰</span>
            <h3 className="font-medium text-gray-900">Manage Revenue</h3>
            <p className="text-sm text-gray-600 mt-1">View and record revenue</p>
          </Link>

          <Link
            to="/app/financial/invoices"
            className="card hover:shadow-md transition-shadow bg-gray-50 hover:bg-gray-100"
          >
            <span className="text-2xl mb-2 block">📄</span>
            <h3 className="font-medium text-gray-900">Manage Invoices</h3>
            <p className="text-sm text-gray-600 mt-1">View and create invoices</p>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Expenses */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Expenses</h2>
            <Link to="/app/financial/expenses" className="text-sm text-blue-600 hover:text-blue-700">
              View All →
            </Link>
          </div>
          {recentExpenses.length > 0 ? (
            <div className="space-y-3">
              {recentExpenses.map((expense: any) => (
                <div key={expense.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{expense.description}</p>
                    <p className="text-sm text-gray-600">
                      {expense.category.replace(/_/g, ' ')} • {new Date(expense.expense_date).toLocaleDateString()}
                    </p>
                    {expense.property_name && (
                      <p className="text-xs text-gray-500">{expense.property_name}</p>
                    )}
                  </div>
                  <div className="ml-4 text-right">
                    <p className="font-semibold text-red-600">
                      -${expense.amount.toFixed(2)}
                    </p>
                    <span className={`text-xs px-2 py-1 rounded ${
                      expense.status === 'paid' ? 'bg-green-100 text-green-800' :
                      expense.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {expense.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No expenses recorded this month</p>
          )}
        </div>

        {/* Recent Revenue */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Revenue</h2>
            <Link to="/app/financial/revenue" className="text-sm text-blue-600 hover:text-blue-700">
              View All →
            </Link>
          </div>
          {recentRevenue.length > 0 ? (
            <div className="space-y-3">
              {recentRevenue.map((revenue: any) => (
                <div key={revenue.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 truncate">{revenue.description}</p>
                    <p className="text-sm text-gray-600">
                      {revenue.source.replace(/_/g, ' ')} • {new Date(revenue.revenue_date).toLocaleDateString()}
                    </p>
                    {revenue.property_name && (
                      <p className="text-xs text-gray-500">{revenue.property_name}</p>
                    )}
                  </div>
                  <div className="ml-4 text-right">
                    <p className="font-semibold text-green-600">
                      +${revenue.amount.toFixed(2)}
                    </p>
                    <span className={`text-xs px-2 py-1 rounded ${
                      revenue.status === 'received' ? 'bg-green-100 text-green-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {revenue.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-8">No revenue recorded this month</p>
          )}
        </div>
      </div>

      {/* Recent Invoices */}
      <div className="card mt-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Invoices</h2>
          <Link to="/app/financial/invoices" className="text-sm text-blue-600 hover:text-blue-700">
            View All →
          </Link>
        </div>
        {recentInvoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Invoice #
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recipient
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {recentInvoices.map((invoice: any) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-blue-600 font-medium">
                        {invoice.invoice_number}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{invoice.recipient_name}</div>
                      {invoice.property_name && (
                        <div className="text-xs text-gray-500">{invoice.property_name}</div>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {new Date(invoice.invoice_date).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right font-semibold text-gray-900">
                      ${invoice.total_amount.toFixed(2)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center">
                      <span className={`text-xs px-2 py-1 rounded ${
                        invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                        invoice.status === 'sent' ? 'bg-blue-100 text-blue-800' :
                        invoice.status === 'overdue' ? 'bg-red-100 text-red-800' :
                        invoice.status === 'cancelled' ? 'bg-gray-100 text-gray-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {invoice.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-8">No invoices created yet</p>
        )}
      </div>
    </div>
  );
}
