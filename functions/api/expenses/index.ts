/**
 * Expenses API - List and Create
 * GET  /api/expenses - List expenses with filters
 * POST /api/expenses - Create a new expense
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// Expense categories (IRS-compliant)
const EXPENSE_CATEGORIES = [
  'utilities',
  'insurance',
  'property_taxes',
  'mortgage_interest',
  'repairs_maintenance',
  'supplies',
  'professional_services',
  'marketing',
  'travel',
  'depreciation',
  'contractor_payments',
  'employee_wages',
  'amenities',
  'linens_replacement',
  'furniture_replacement',
  'improvements',
  'equipment',
];

// GET /api/expenses
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    // Query parameters
    const propertyId = url.searchParams.get('property_id');
    const category = url.searchParams.get('category');
    const status = url.searchParams.get('status');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');
    const limit = parseInt(url.searchParams.get('limit') || '100');

    // Build query
    let query = `
      SELECT
        e.id, e.property_id, e.category, e.vendor, e.description,
        e.amount, e.tax_deductible, e.business_percentage,
        e.expense_date, e.due_date, e.paid_date,
        e.status, e.payment_method, e.receipt_url,
        e.created_at, e.updated_at,
        p.name as property_name
      FROM expenses e
      LEFT JOIN property p ON e.property_id = p.id
      WHERE 1=1
    `;

    const params: any[] = [];

    // Filter by property ownership (admins see all)
    if (user.role !== 'admin') {
      query += ' AND (e.property_id IS NULL OR p.owner_id = ?)';
      params.push(user.userId);
    }

    // Apply filters
    if (propertyId) {
      query += ' AND e.property_id = ?';
      params.push(propertyId);
    }

    if (category) {
      query += ' AND e.category = ?';
      params.push(category);
    }

    if (status) {
      query += ' AND e.status = ?';
      params.push(status);
    }

    if (startDate) {
      query += ' AND e.expense_date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND e.expense_date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY e.expense_date DESC, e.created_at DESC LIMIT ?';
    params.push(limit);

    const expenses = await env.DB.prepare(query).bind(...params).all();

    // Calculate summary statistics
    let totalAmount = 0;
    let totalDeductible = 0;
    let paidAmount = 0;
    let pendingAmount = 0;

    expenses.results?.forEach((expense: any) => {
      totalAmount += expense.amount || 0;
      const deductible = expense.tax_deductible
        ? (expense.amount * (expense.business_percentage / 100))
        : 0;
      totalDeductible += deductible;

      if (expense.status === 'paid') {
        paidAmount += expense.amount || 0;
      } else {
        pendingAmount += expense.amount || 0;
      }
    });

    return new Response(
      JSON.stringify({
        success: true,
        expenses: expenses.results || [],
        count: expenses.results?.length || 0,
        summary: {
          total_amount: totalAmount,
          total_deductible: totalDeductible,
          paid_amount: paidAmount,
          pending_amount: pendingAmount,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Expenses GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch expenses',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/expenses
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.category || !data.description || !data.amount) {
      return new Response(
        JSON.stringify({ error: 'Category, description, and amount are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate category
    if (!EXPENSE_CATEGORIES.includes(data.category)) {
      return new Response(
        JSON.stringify({
          error: 'Invalid category',
          valid_categories: EXPENSE_CATEGORIES,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate amount
    const amount = parseFloat(data.amount);
    if (isNaN(amount) || amount <= 0) {
      return new Response(
        JSON.stringify({ error: 'Amount must be a positive number' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // If property_id specified, verify access
    if (data.property_id) {
      const property = await env.DB.prepare(
        'SELECT id, owner_id FROM property WHERE id = ?'
      )
        .bind(data.property_id)
        .first();

      if (!property) {
        return new Response(
          JSON.stringify({ error: 'Property not found' }),
          {
            status: 404,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      if (user.role !== 'admin' && property.owner_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied to this property' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Create expense
    const result = await env.DB.prepare(
      `INSERT INTO expenses (
        property_id, category, vendor, description, amount,
        tax_deductible, business_percentage, expense_date,
        due_date, status, payment_method, created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.property_id || null,
        data.category,
        data.vendor || null,
        data.description,
        amount,
        data.tax_deductible !== false ? 1 : 0,
        data.business_percentage || 100,
        data.expense_date || new Date().toISOString().split('T')[0],
        data.due_date || null,
        data.status || 'draft',
        data.payment_method || null,
        user.userId
      )
      .run();

    // Fetch created expense
    const expense = await env.DB.prepare(
      `SELECT
        e.id, e.property_id, e.category, e.vendor, e.description,
        e.amount, e.tax_deductible, e.business_percentage,
        e.expense_date, e.due_date, e.paid_date,
        e.status, e.payment_method, e.created_at,
        p.name as property_name
      FROM expenses e
      LEFT JOIN property p ON e.property_id = p.id
      WHERE e.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        expense,
        message: 'Expense created successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Expenses POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create expense',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
