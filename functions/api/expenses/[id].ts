/**
 * Expenses API - Get, Update, Delete by ID
 * GET    /api/expenses/[id] - Get expense details
 * PUT    /api/expenses/[id] - Update expense
 * DELETE /api/expenses/[id] - Delete expense
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/expenses/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const expenseId = params.id as string;

    const expense = await env.DB.prepare(
      `SELECT
        e.id, e.property_id, e.category, e.vendor, e.description,
        e.amount, e.tax_deductible, e.business_percentage,
        e.expense_date, e.due_date, e.paid_date,
        e.status, e.payment_method, e.check_number,
        e.receipt_url, e.receipt_filename,
        e.invoice_id, e.task_id,
        e.created_at, e.updated_at,
        e.created_by_id, e.approved_by_id,
        p.name as property_name,
        p.address as property_address,
        creator.first_name as creator_first_name,
        creator.last_name as creator_last_name
      FROM expenses e
      LEFT JOIN property p ON e.property_id = p.id
      LEFT JOIN users creator ON e.created_by_id = creator.id
      WHERE e.id = ?`
    )
      .bind(expenseId)
      .first();

    if (!expense) {
      return new Response(
        JSON.stringify({ error: 'Expense not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      if (expense.property_id) {
        const property = await env.DB.prepare(
          'SELECT owner_id FROM property WHERE id = ?'
        )
          .bind(expense.property_id)
          .first();

        if (property && property.owner_id !== user.userId) {
          return new Response(
            JSON.stringify({ error: 'Access denied' }),
            {
              status: 403,
              headers: { 'Content-Type': 'application/json' },
            }
          );
        }
      } else if (expense.created_by_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Calculate deductible amount
    const deductible_amount = expense.tax_deductible
      ? (expense.amount * (expense.business_percentage / 100))
      : 0;

    return new Response(
      JSON.stringify({
        success: true,
        expense: {
          ...expense,
          deductible_amount,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Expenses GET by ID] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch expense',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/expenses/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const expenseId = params.id as string;
    const data = await request.json();

    // Fetch existing expense
    const expense = await env.DB.prepare(
      'SELECT * FROM expenses WHERE id = ?'
    )
      .bind(expenseId)
      .first();

    if (!expense) {
      return new Response(
        JSON.stringify({ error: 'Expense not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      if (expense.property_id) {
        const property = await env.DB.prepare(
          'SELECT owner_id FROM property WHERE id = ?'
        )
          .bind(expense.property_id)
          .first();

        if (property && property.owner_id !== user.userId) {
          return new Response(
            JSON.stringify({ error: 'Access denied' }),
            {
              status: 403,
              headers: { 'Content-Type': 'application/json' },
            }
          );
        }
      } else if (expense.created_by_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Build update query dynamically
    const updates: string[] = [];
    const params: any[] = [];

    if (data.category !== undefined) {
      updates.push('category = ?');
      params.push(data.category);
    }
    if (data.vendor !== undefined) {
      updates.push('vendor = ?');
      params.push(data.vendor);
    }
    if (data.description !== undefined) {
      updates.push('description = ?');
      params.push(data.description);
    }
    if (data.amount !== undefined) {
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
      updates.push('amount = ?');
      params.push(amount);
    }
    if (data.tax_deductible !== undefined) {
      updates.push('tax_deductible = ?');
      params.push(data.tax_deductible ? 1 : 0);
    }
    if (data.business_percentage !== undefined) {
      updates.push('business_percentage = ?');
      params.push(data.business_percentage);
    }
    if (data.expense_date !== undefined) {
      updates.push('expense_date = ?');
      params.push(data.expense_date);
    }
    if (data.due_date !== undefined) {
      updates.push('due_date = ?');
      params.push(data.due_date);
    }
    if (data.paid_date !== undefined) {
      updates.push('paid_date = ?');
      params.push(data.paid_date);
    }
    if (data.status !== undefined) {
      updates.push('status = ?');
      params.push(data.status);
    }
    if (data.payment_method !== undefined) {
      updates.push('payment_method = ?');
      params.push(data.payment_method);
    }
    if (data.check_number !== undefined) {
      updates.push('check_number = ?');
      params.push(data.check_number);
    }
    if (data.receipt_url !== undefined) {
      updates.push('receipt_url = ?');
      params.push(data.receipt_url);
    }

    if (updates.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No fields to update' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Always update updated_at
    updates.push('updated_at = datetime("now")');
    params.push(expenseId);

    // Execute update
    await env.DB.prepare(
      `UPDATE expenses SET ${updates.join(', ')} WHERE id = ?`
    )
      .bind(...params)
      .run();

    // Fetch updated expense
    const updatedExpense = await env.DB.prepare(
      `SELECT
        e.id, e.property_id, e.category, e.vendor, e.description,
        e.amount, e.tax_deductible, e.business_percentage,
        e.expense_date, e.due_date, e.paid_date,
        e.status, e.payment_method, e.created_at, e.updated_at,
        p.name as property_name
      FROM expenses e
      LEFT JOIN property p ON e.property_id = p.id
      WHERE e.id = ?`
    )
      .bind(expenseId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        expense: updatedExpense,
        message: 'Expense updated successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Expenses PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to update expense',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/expenses/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const expenseId = params.id as string;

    // Fetch expense
    const expense = await env.DB.prepare(
      'SELECT * FROM expenses WHERE id = ?'
    )
      .bind(expenseId)
      .first();

    if (!expense) {
      return new Response(
        JSON.stringify({ error: 'Expense not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights (only admin or creator can delete)
    if (user.role !== 'admin' && expense.created_by_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete expense
    await env.DB.prepare('DELETE FROM expenses WHERE id = ?')
      .bind(expenseId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Expense deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Expenses DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete expense',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
