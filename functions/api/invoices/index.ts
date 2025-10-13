/**
 * Invoices API with Line Items
 * GET  /api/invoices - List invoices
 * POST /api/invoices - Create invoice with line items
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/invoices
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);
    const propertyId = url.searchParams.get('property_id');
    const workerId = url.searchParams.get('worker_id');
    const status = url.searchParams.get('status');

    let query = `
      SELECT
        i.*,
        p.name as property_name,
        w.first_name || ' ' || w.last_name as worker_name
      FROM invoices i
      LEFT JOIN property p ON i.property_id = p.id
      LEFT JOIN users w ON i.worker_id = w.id
      WHERE 1=1
    `;

    const bindings: any[] = [];

    if (propertyId) {
      query += ' AND i.property_id = ?';
      bindings.push(propertyId);
    }

    if (workerId) {
      query += ' AND i.worker_id = ?';
      bindings.push(workerId);
    }

    if (status) {
      query += ' AND i.status = ?';
      bindings.push(status);
    }

    // Property owners can only see invoices for their properties
    if (user.role === 'property_owner') {
      query += ' AND p.owner_id = ?';
      bindings.push(user.userId);
    }

    // Workers can only see their own invoices
    if (user.role === 'service_staff') {
      query += ' AND i.worker_id = ?';
      bindings.push(user.userId);
    }

    query += ' ORDER BY i.created_at DESC';

    const stmt = env.DB.prepare(query);
    const invoices = await (bindings.length > 0
      ? stmt.bind(...bindings)
      : stmt
    ).all();

    // Get line items for each invoice
    const invoicesWithItems = await Promise.all(
      (invoices.results || []).map(async (invoice: any) => {
        const items = await env.DB.prepare(
          'SELECT * FROM invoice_line_item WHERE invoice_id = ?'
        )
          .bind(invoice.id)
          .all();

        return {
          ...invoice,
          line_items: items.results || [],
        };
      })
    );

    return new Response(
      JSON.stringify({
        success: true,
        invoices: invoicesWithItems,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoices GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch invoices',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/invoices
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();
    const {
      property_id,
      worker_id,
      title,
      description,
      recipient_name,
      recipient_email,
      recipient_address,
      invoice_date,
      due_date,
      tax_rate = 0,
      discount_amount = 0,
      notes,
      terms,
      line_items = [],
    } = data;

    if (!title || !recipient_name || !line_items || line_items.length === 0) {
      return new Response(
        JSON.stringify({ error: 'title, recipient_name, and at least one line_item are required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Calculate totals
    const subtotal = line_items.reduce((sum: number, item: any) => {
      return sum + (item.unit_price * item.quantity);
    }, 0);

    const tax_amount = subtotal * (tax_rate / 100);
    const total_amount = subtotal + tax_amount - discount_amount;

    // Generate invoice number
    const invoiceCount = await env.DB.prepare(
      'SELECT COUNT(*) as count FROM invoices'
    ).first();
    const invoiceNumber = `INV-$${String((invoiceCount as any).count + 1).padStart(5, '0')}`;

    // Create invoice
    await env.DB.prepare(
      `INSERT INTO invoices (
        property_id,
        invoice_number,
        title,
        description,
        recipient_name,
        recipient_email,
        recipient_address,
        subtotal,
        tax_rate,
        tax_amount,
        discount_amount,
        total_amount,
        invoice_date,
        due_date,
        notes,
        terms,
        status,
        worker_id,
        created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        property_id || null,
        invoiceNumber,
        title,
        description || null,
        recipient_name,
        recipient_email || null,
        recipient_address || null,
        subtotal,
        tax_rate,
        tax_amount,
        discount_amount,
        total_amount,
        invoice_date || new Date().toISOString().split('T')[0],
        due_date || null,
        notes || null,
        terms || null,
        'draft',
        worker_id || null,
        user.userId
      )
      .run();

    // Get the created invoice
    const invoice = await env.DB.prepare(
      'SELECT * FROM invoices WHERE invoice_number = ?'
    )
      .bind(invoiceNumber)
      .first();

    // Create line items
    for (const item of line_items) {
      const itemTotal = item.unit_price * item.quantity;
      await env.DB.prepare(
        `INSERT INTO invoice_line_item (
          invoice_id,
          service_price_id,
          description,
          quantity,
          unit_price,
          total
        ) VALUES (?, ?, ?, ?, ?, ?)`
      )
        .bind(
          (invoice as any).id,
          item.service_price_id || null,
          item.description,
          item.quantity,
          item.unit_price,
          itemTotal
        )
        .run();
    }

    // Get invoice with line items
    const items = await env.DB.prepare(
      'SELECT * FROM invoice_line_item WHERE invoice_id = ?'
    )
      .bind((invoice as any).id)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Invoice created successfully',
        invoice: {
          ...invoice,
          line_items: items.results || [],
        },
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoices POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to create invoice',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
