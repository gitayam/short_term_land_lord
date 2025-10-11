/**
 * Invoices API - Get, Update, Delete by ID
 * GET    /api/invoices/[id] - Get invoice details with line items
 * PUT    /api/invoices/[id] - Update invoice
 * DELETE /api/invoices/[id] - Delete invoice
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/invoices/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const invoiceId = params.id as string;

    const invoice = await env.DB.prepare(
      `SELECT
        i.id, i.invoice_number, i.title, i.description,
        i.property_id, i.booking_id,
        i.recipient_name, i.recipient_email, i.recipient_address,
        i.subtotal, i.tax_rate, i.tax_amount,
        i.discount_amount, i.total_amount,
        i.invoice_date, i.due_date, i.paid_date,
        i.status, i.payment_method, i.notes, i.terms,
        i.created_at, i.updated_at,
        i.created_by_id,
        p.name as property_name,
        p.address as property_address,
        creator.first_name as creator_first_name,
        creator.last_name as creator_last_name
      FROM invoices i
      LEFT JOIN property p ON i.property_id = p.id
      LEFT JOIN users creator ON i.created_by_id = creator.id
      WHERE i.id = ?`
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

    // Fetch line items
    const items = await env.DB.prepare(
      `SELECT id, description, quantity, unit_price, amount, item_type, created_at
       FROM invoice_items WHERE invoice_id = ?
       ORDER BY id ASC`
    )
      .bind(invoiceId)
      .all();

    // Fetch payments
    const payments = await env.DB.prepare(
      `SELECT
        ip.id, ip.amount, ip.payment_date, ip.payment_method,
        ip.transaction_id, ip.reference_number, ip.notes,
        ip.created_at,
        u.first_name as creator_first_name,
        u.last_name as creator_last_name
      FROM invoice_payments ip
      LEFT JOIN users u ON ip.created_by_id = u.id
      WHERE ip.invoice_id = ?
      ORDER BY ip.payment_date DESC, ip.created_at DESC`
    )
      .bind(invoiceId)
      .all();

    // Calculate paid amount and balance
    let paidAmount = 0;
    payments.results?.forEach((payment: any) => {
      paidAmount += payment.amount || 0;
    });

    const balanceDue = invoice.total_amount - paidAmount;

    return new Response(
      JSON.stringify({
        success: true,
        invoice: {
          ...invoice,
          items: items.results || [],
          payments: payments.results || [],
          paid_amount: paidAmount,
          balance_due: balanceDue,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoices GET by ID] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch invoice',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/invoices/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const invoiceId = params.id as string;
    const data = await request.json();

    // Fetch existing invoice
    const invoice = await env.DB.prepare(
      'SELECT * FROM invoices WHERE id = ?'
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

    // Build update query dynamically
    const updates: string[] = [];
    const params: any[] = [];

    if (data.title !== undefined) {
      updates.push('title = ?');
      params.push(data.title);
    }
    if (data.description !== undefined) {
      updates.push('description = ?');
      params.push(data.description);
    }
    if (data.recipient_name !== undefined) {
      updates.push('recipient_name = ?');
      params.push(data.recipient_name);
    }
    if (data.recipient_email !== undefined) {
      updates.push('recipient_email = ?');
      params.push(data.recipient_email);
    }
    if (data.recipient_address !== undefined) {
      updates.push('recipient_address = ?');
      params.push(data.recipient_address);
    }
    if (data.invoice_date !== undefined) {
      updates.push('invoice_date = ?');
      params.push(data.invoice_date);
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
    if (data.notes !== undefined) {
      updates.push('notes = ?');
      params.push(data.notes);
    }
    if (data.terms !== undefined) {
      updates.push('terms = ?');
      params.push(data.terms);
    }

    // Handle line items update
    if (data.items && Array.isArray(data.items)) {
      // Recalculate totals
      let subtotal = 0;
      for (const item of data.items) {
        if (!item.description || !item.unit_price) {
          return new Response(
            JSON.stringify({
              error: 'Each line item must have description and unit_price',
            }),
            {
              status: 400,
              headers: { 'Content-Type': 'application/json' },
            }
          );
        }
        const quantity = item.quantity || 1;
        const unitPrice = parseFloat(item.unit_price);
        subtotal += quantity * unitPrice;
      }

      const taxRate = data.tax_rate !== undefined ? parseFloat(data.tax_rate) : invoice.tax_rate;
      const taxAmount = subtotal * (taxRate / 100);
      const discountAmount = data.discount_amount !== undefined ? parseFloat(data.discount_amount) : invoice.discount_amount;
      const totalAmount = subtotal + taxAmount - discountAmount;

      updates.push('subtotal = ?');
      params.push(subtotal);
      updates.push('tax_rate = ?');
      params.push(taxRate);
      updates.push('tax_amount = ?');
      params.push(taxAmount);
      updates.push('discount_amount = ?');
      params.push(discountAmount);
      updates.push('total_amount = ?');
      params.push(totalAmount);

      // Delete existing items and create new ones
      await env.DB.prepare('DELETE FROM invoice_items WHERE invoice_id = ?')
        .bind(invoiceId)
        .run();

      for (const item of data.items) {
        const quantity = item.quantity || 1;
        const unitPrice = parseFloat(item.unit_price);
        const amount = quantity * unitPrice;

        await env.DB.prepare(
          `INSERT INTO invoice_items (
            invoice_id, description, quantity, unit_price, amount, item_type
          ) VALUES (?, ?, ?, ?, ?, ?)`
        )
          .bind(
            invoiceId,
            item.description,
            quantity,
            unitPrice,
            amount,
            item.item_type || null
          )
          .run();
      }
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
    params.push(invoiceId);

    // Execute update
    await env.DB.prepare(
      `UPDATE invoices SET ${updates.join(', ')} WHERE id = ?`
    )
      .bind(...params)
      .run();

    // Fetch updated invoice
    const updatedInvoice = await env.DB.prepare(
      `SELECT
        i.id, i.invoice_number, i.title, i.description,
        i.property_id, i.recipient_name,
        i.subtotal, i.tax_rate, i.tax_amount,
        i.discount_amount, i.total_amount,
        i.invoice_date, i.due_date, i.status,
        i.created_at, i.updated_at,
        p.name as property_name
      FROM invoices i
      LEFT JOIN property p ON i.property_id = p.id
      WHERE i.id = ?`
    )
      .bind(invoiceId)
      .first();

    const items = await env.DB.prepare(
      `SELECT id, description, quantity, unit_price, amount, item_type
       FROM invoice_items WHERE invoice_id = ?`
    )
      .bind(invoiceId)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        invoice: {
          ...updatedInvoice,
          items: items.results || [],
        },
        message: 'Invoice updated successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoices PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to update invoice',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/invoices/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const invoiceId = params.id as string;

    // Fetch invoice
    const invoice = await env.DB.prepare(
      'SELECT * FROM invoices WHERE id = ?'
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

    // Check access rights (only admin or creator can delete)
    if (user.role !== 'admin' && invoice.created_by_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Prevent deletion of paid invoices
    if (invoice.status === 'paid') {
      return new Response(
        JSON.stringify({
          error: 'Cannot delete paid invoices',
          suggestion: 'Consider cancelling the invoice instead',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete invoice (cascades to items and payments via foreign key)
    await env.DB.prepare('DELETE FROM invoices WHERE id = ?')
      .bind(invoiceId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Invoice deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoices DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete invoice',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
