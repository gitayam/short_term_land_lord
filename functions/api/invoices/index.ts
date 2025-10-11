/**
 * Invoices API - List and Create
 * GET  /api/invoices - List invoices with filters
 * POST /api/invoices - Create a new invoice with line items
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// Invoice statuses
const INVOICE_STATUSES = ['draft', 'sent', 'paid', 'overdue', 'cancelled'];

// Generate invoice number in format: INV-YYYYMMDD-XXXX
async function generateInvoiceNumber(env: Env): Promise<string> {
  const now = new Date();
  const dateStr = now.toISOString().split('T')[0].replace(/-/g, '');

  // Get count of invoices created today
  const result = await env.DB.prepare(
    `SELECT COUNT(*) as count FROM invoices
     WHERE invoice_number LIKE ?`
  )
    .bind(`INV-${dateStr}-%`)
    .first();

  const count = (result?.count as number) || 0;
  const sequence = String(count + 1).padStart(4, '0');

  return `INV-${dateStr}-${sequence}`;
}

// GET /api/invoices
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    // Query parameters
    const propertyId = url.searchParams.get('property_id');
    const bookingId = url.searchParams.get('booking_id');
    const status = url.searchParams.get('status');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');
    const limit = parseInt(url.searchParams.get('limit') || '100');

    // Build query
    let query = `
      SELECT
        i.id, i.invoice_number, i.title, i.description,
        i.property_id, i.booking_id,
        i.recipient_name, i.recipient_email, i.recipient_address,
        i.subtotal, i.tax_rate, i.tax_amount,
        i.discount_amount, i.total_amount,
        i.invoice_date, i.due_date, i.paid_date,
        i.status, i.payment_method, i.notes, i.terms,
        i.created_at, i.updated_at,
        p.name as property_name,
        p.address as property_address
      FROM invoices i
      LEFT JOIN property p ON i.property_id = p.id
      WHERE 1=1
    `;

    const params: any[] = [];

    // Filter by property ownership (admins see all)
    if (user.role !== 'admin') {
      query += ' AND p.owner_id = ?';
      params.push(user.userId);
    }

    // Apply filters
    if (propertyId) {
      query += ' AND i.property_id = ?';
      params.push(propertyId);
    }

    if (bookingId) {
      query += ' AND i.booking_id = ?';
      params.push(bookingId);
    }

    if (status) {
      query += ' AND i.status = ?';
      params.push(status);
    }

    if (startDate) {
      query += ' AND i.invoice_date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND i.invoice_date <= ?';
      params.push(endDate);
    }

    query += ' ORDER BY i.invoice_date DESC, i.created_at DESC LIMIT ?';
    params.push(limit);

    const invoices = await env.DB.prepare(query).bind(...params).all();

    // Calculate summary statistics
    let totalAmount = 0;
    let paidAmount = 0;
    let pendingAmount = 0;
    let overdueAmount = 0;

    invoices.results?.forEach((inv: any) => {
      totalAmount += inv.total_amount || 0;
      if (inv.status === 'paid') {
        paidAmount += inv.total_amount || 0;
      } else if (inv.status === 'overdue') {
        overdueAmount += inv.total_amount || 0;
      } else if (inv.status === 'sent' || inv.status === 'draft') {
        pendingAmount += inv.total_amount || 0;
      }
    });

    return new Response(
      JSON.stringify({
        success: true,
        invoices: invoices.results || [],
        count: invoices.results?.length || 0,
        summary: {
          total_amount: totalAmount,
          paid_amount: paidAmount,
          pending_amount: pendingAmount,
          overdue_amount: overdueAmount,
        },
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
        status: error.message.includes('Unauthorized') ? 401 : 500,
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

    // Validate required fields
    if (!data.title || !data.recipient_name || !data.items || !Array.isArray(data.items) || data.items.length === 0) {
      return new Response(
        JSON.stringify({
          error: 'Title, recipient name, and at least one line item are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify property access if property_id provided
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

    // Calculate totals from line items
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
      if (isNaN(unitPrice) || unitPrice < 0) {
        return new Response(
          JSON.stringify({ error: 'Invalid unit_price in line items' }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
      subtotal += quantity * unitPrice;
    }

    // Calculate tax and total
    const taxRate = parseFloat(data.tax_rate || '0');
    const taxAmount = subtotal * (taxRate / 100);
    const discountAmount = parseFloat(data.discount_amount || '0');
    const totalAmount = subtotal + taxAmount - discountAmount;

    // Generate invoice number
    const invoiceNumber = await generateInvoiceNumber(env);

    // Create invoice
    const invoiceResult = await env.DB.prepare(
      `INSERT INTO invoices (
        property_id, booking_id, invoice_number, title, description,
        recipient_name, recipient_email, recipient_address,
        subtotal, tax_rate, tax_amount, discount_amount, total_amount,
        invoice_date, due_date, status, notes, terms, created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.property_id || null,
        data.booking_id || null,
        invoiceNumber,
        data.title,
        data.description || null,
        data.recipient_name,
        data.recipient_email || null,
        data.recipient_address || null,
        subtotal,
        taxRate,
        taxAmount,
        discountAmount,
        totalAmount,
        data.invoice_date || new Date().toISOString().split('T')[0],
        data.due_date || null,
        data.status || 'draft',
        data.notes || null,
        data.terms || null,
        user.userId
      )
      .run();

    const invoiceId = invoiceResult.meta.last_row_id;

    // Create line items
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

    // Fetch created invoice with items
    const invoice = await env.DB.prepare(
      `SELECT
        i.id, i.invoice_number, i.title, i.description,
        i.property_id, i.booking_id,
        i.recipient_name, i.recipient_email, i.recipient_address,
        i.subtotal, i.tax_rate, i.tax_amount,
        i.discount_amount, i.total_amount,
        i.invoice_date, i.due_date, i.status,
        i.notes, i.terms, i.created_at,
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
          ...invoice,
          items: items.results || [],
        },
        message: 'Invoice created successfully',
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
        error: 'Failed to create invoice',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
