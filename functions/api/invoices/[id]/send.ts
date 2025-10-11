/**
 * Invoice Send API
 * POST /api/invoices/[id]/send - Send invoice via email
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';
import { sendEmail } from '../../../utils/email';

// POST /api/invoices/[id]/send
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const invoiceId = params.id as string;

    // Fetch invoice
    const invoice = await env.DB.prepare(
      `SELECT
        i.id, i.invoice_number, i.title, i.description,
        i.property_id, i.recipient_name, i.recipient_email,
        i.total_amount, i.invoice_date, i.due_date,
        i.status, i.created_by_id,
        p.name as property_name,
        p.address as property_address
      FROM invoices i
      LEFT JOIN property p ON i.property_id = p.id
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

    // Validate recipient email
    if (!invoice.recipient_email) {
      return new Response(
        JSON.stringify({
          error: 'Cannot send invoice without recipient email',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Fetch line items
    const items = await env.DB.prepare(
      `SELECT description, quantity, unit_price, amount
       FROM invoice_items WHERE invoice_id = ?
       ORDER BY id ASC`
    )
      .bind(invoiceId)
      .all();

    // Build email content
    const itemsHtml = (items.results || [])
      .map(
        (item: any) => `
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">${item.description}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: center;">${item.quantity}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">$${item.unit_price.toFixed(2)}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: right;">$${item.amount.toFixed(2)}</td>
        </tr>
      `
      )
      .join('');

    const propertyInfo = invoice.property_name
      ? `<p><strong>Property:</strong> ${invoice.property_name}</p>
         ${invoice.property_address ? `<p><strong>Address:</strong> ${invoice.property_address}</p>` : ''}`
      : '';

    const dueDate = invoice.due_date
      ? `<p><strong>Due Date:</strong> ${new Date(invoice.due_date).toLocaleDateString()}</p>`
      : '';

    const htmlContent = `
      <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #1f2937;">Invoice ${invoice.invoice_number}</h2>

        <div style="background-color: #f9fafb; padding: 16px; border-radius: 8px; margin-bottom: 24px;">
          <h3 style="margin-top: 0;">${invoice.title}</h3>
          ${invoice.description ? `<p>${invoice.description}</p>` : ''}
          ${propertyInfo}
          <p><strong>Invoice Date:</strong> ${new Date(invoice.invoice_date).toLocaleDateString()}</p>
          ${dueDate}
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
          <thead>
            <tr style="background-color: #f3f4f6;">
              <th style="padding: 8px; text-align: left; border-bottom: 2px solid #e5e7eb;">Description</th>
              <th style="padding: 8px; text-align: center; border-bottom: 2px solid #e5e7eb;">Qty</th>
              <th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Unit Price</th>
              <th style="padding: 8px; text-align: right; border-bottom: 2px solid #e5e7eb;">Amount</th>
            </tr>
          </thead>
          <tbody>
            ${itemsHtml}
          </tbody>
        </table>

        <div style="text-align: right; margin-bottom: 24px;">
          <p style="font-size: 18px; margin: 8px 0;"><strong>Total: $${invoice.total_amount.toFixed(2)}</strong></p>
        </div>

        <div style="background-color: #eff6ff; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6;">
          <p style="margin: 0; color: #1e40af;">
            Please remit payment by ${invoice.due_date ? new Date(invoice.due_date).toLocaleDateString() : 'the due date'}.
          </p>
        </div>

        <p style="color: #6b7280; font-size: 12px; margin-top: 24px;">
          If you have any questions about this invoice, please contact us.
        </p>
      </div>
    `;

    // Send email
    try {
      await sendEmail(env, {
        to: invoice.recipient_email,
        subject: `Invoice ${invoice.invoice_number} - ${invoice.title}`,
        text: `Invoice ${invoice.invoice_number}\n\n${invoice.title}\n${invoice.description || ''}\n\nTotal: $${invoice.total_amount.toFixed(2)}\n\nPlease view the full invoice in your email client that supports HTML.`,
        html: htmlContent,
      });
    } catch (emailError: any) {
      console.error('[Invoice Send] Email error:', emailError);
      // Continue even if email fails - update status anyway
    }

    // Update invoice status to "sent" if it was "draft"
    if (invoice.status === 'draft') {
      await env.DB.prepare(
        `UPDATE invoices
         SET status = 'sent', updated_at = datetime('now')
         WHERE id = ?`
      )
        .bind(invoiceId)
        .run();
    }

    // Fetch updated invoice
    const updatedInvoice = await env.DB.prepare(
      `SELECT
        i.id, i.invoice_number, i.title, i.status,
        i.invoice_date, i.due_date, i.total_amount,
        i.recipient_name, i.recipient_email
      FROM invoices i
      WHERE i.id = ?`
    )
      .bind(invoiceId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        invoice: updatedInvoice,
        message: `Invoice sent to ${invoice.recipient_email}`,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Invoice Send] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to send invoice',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
