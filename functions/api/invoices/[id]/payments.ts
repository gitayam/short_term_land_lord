/**
 * Invoice Payments API
 * GET  /api/invoices/[id]/payments - List payments for an invoice
 * POST /api/invoices/[id]/payments - Record a payment against an invoice
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

// GET /api/invoices/[id]/payments
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const invoiceId = params.id as string;

    // Verify invoice exists and user has access
    const invoice = await env.DB.prepare(
      `SELECT i.id, i.property_id, i.created_by_id, i.total_amount
       FROM invoices i WHERE i.id = ?`
    )
      .bind(invoiceId)
      .first();

    if (!invoice) {
      return new Response(
        JSON.stringify({ error: 'Invoice not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      if (invoice.property_id) {
        const property = await env.DB.prepare(
          'SELECT owner_id FROM property WHERE id = ?'
        )
          .bind(invoice.property_id)
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
      } else if (invoice.created_by_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Fetch payments
    const payments = await env.DB.prepare(
      `SELECT
        ip.id, ip.amount, ip.payment_date, ip.payment_method,
        ip.transaction_id, ip.reference_number, ip.notes,
        ip.created_at,
        u.first_name as creator_first_name,
        u.last_name as creator_last_name,
        u.email as creator_email
      FROM invoice_payments ip
      LEFT JOIN users u ON ip.created_by_id = u.id
      WHERE ip.invoice_id = ?
      ORDER BY ip.payment_date DESC, ip.created_at DESC`
    )
      .bind(invoiceId)
      .all();

    // Calculate totals
    let totalPaid = 0;
    payments.results?.forEach((payment: any) => {
      totalPaid += payment.amount || 0;
    });

    const balanceDue = invoice.total_amount - totalPaid;

    return new Response(
      JSON.stringify({
        success: true,
        payments: payments.results || [],
        count: payments.results?.length || 0,
        summary: {
          invoice_total: invoice.total_amount,
          total_paid: totalPaid,
          balance_due: balanceDue,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoice Payments GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch payments',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/invoices/[id]/payments
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const invoiceId = params.id as string;
    const data = await request.json();

    // Validate required fields
    if (!data.amount) {
      return new Response(
        JSON.stringify({
          error: 'Payment amount is required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

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

    // Verify invoice exists and user has access
    const invoice = await env.DB.prepare(
      `SELECT i.id, i.property_id, i.created_by_id, i.total_amount, i.status
       FROM invoices i WHERE i.id = ?`
    )
      .bind(invoiceId)
      .first();

    if (!invoice) {
      return new Response(
        JSON.stringify({ error: 'Invoice not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      if (invoice.property_id) {
        const property = await env.DB.prepare(
          'SELECT owner_id FROM property WHERE id = ?'
        )
          .bind(invoice.property_id)
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
      } else if (invoice.created_by_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Calculate existing paid amount
    const existingPayments = await env.DB.prepare(
      `SELECT COALESCE(SUM(amount), 0) as total_paid
       FROM invoice_payments WHERE invoice_id = ?`
    )
      .bind(invoiceId)
      .first();

    const totalPaid = (existingPayments?.total_paid as number) || 0;
    const balanceDue = invoice.total_amount - totalPaid;

    // Validate payment doesn't exceed balance
    if (amount > balanceDue) {
      return new Response(
        JSON.stringify({
          error: 'Payment amount exceeds balance due',
          balance_due: balanceDue,
          payment_amount: amount,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create payment record
    const result = await env.DB.prepare(
      `INSERT INTO invoice_payments (
        invoice_id, amount, payment_date, payment_method,
        transaction_id, reference_number, notes, created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        invoiceId,
        amount,
        data.payment_date || new Date().toISOString().split('T')[0],
        data.payment_method || null,
        data.transaction_id || null,
        data.reference_number || null,
        data.notes || null,
        user.userId
      )
      .run();

    // Calculate new balance
    const newTotalPaid = totalPaid + amount;
    const newBalanceDue = invoice.total_amount - newTotalPaid;

    // Update invoice status if fully paid
    if (newBalanceDue <= 0.01) {
      // Allow for rounding errors
      await env.DB.prepare(
        `UPDATE invoices
         SET status = 'paid',
             paid_date = ?,
             payment_method = ?,
             updated_at = datetime('now')
         WHERE id = ?`
      )
        .bind(
          data.payment_date || new Date().toISOString().split('T')[0],
          data.payment_method || null,
          invoiceId
        )
        .run();
    }

    // Fetch created payment
    const payment = await env.DB.prepare(
      `SELECT
        ip.id, ip.amount, ip.payment_date, ip.payment_method,
        ip.transaction_id, ip.reference_number, ip.notes,
        ip.created_at,
        u.first_name as creator_first_name,
        u.last_name as creator_last_name
      FROM invoice_payments ip
      LEFT JOIN users u ON ip.created_by_id = u.id
      WHERE ip.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        payment,
        invoice_status: {
          invoice_total: invoice.total_amount,
          total_paid: newTotalPaid,
          balance_due: newBalanceDue,
          is_fully_paid: newBalanceDue <= 0.01,
        },
        message: 'Payment recorded successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoice Payments POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to record payment',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
