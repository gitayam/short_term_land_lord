/**
 * Messages API (Internal Messaging)
 * GET  /api/messages - List messages (inbox/sent)
 * POST /api/messages - Send new message
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/messages
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    const type = url.searchParams.get('type') || 'inbox'; // inbox, sent, unread
    const propertyId = url.searchParams.get('property_id');
    const limit = parseInt(url.searchParams.get('limit') || '50');

    let query = `
      SELECT
        m.id, m.sender_id, m.recipient_id, m.subject, m.body,
        m.message_type, m.priority, m.is_read, m.read_at,
        m.parent_message_id, m.property_id, m.created_at,
        sender.first_name as sender_first_name,
        sender.last_name as sender_last_name,
        sender.email as sender_email,
        recipient.first_name as recipient_first_name,
        recipient.last_name as recipient_last_name,
        recipient.email as recipient_email,
        p.name as property_name
      FROM message m
      LEFT JOIN users sender ON m.sender_id = sender.id
      LEFT JOIN users recipient ON m.recipient_id = recipient.id
      LEFT JOIN property p ON m.property_id = p.id
      WHERE 1=1
    `;

    const params: any[] = [];

    if (type === 'inbox') {
      query += ' AND m.recipient_id = ?';
      params.push(user.userId);
    } else if (type === 'sent') {
      query += ' AND m.sender_id = ?';
      params.push(user.userId);
    } else if (type === 'unread') {
      query += ' AND m.recipient_id = ? AND m.is_read = 0';
      params.push(user.userId);
    }

    if (propertyId) {
      query += ' AND m.property_id = ?';
      params.push(propertyId);
    }

    query += ' ORDER BY m.created_at DESC LIMIT ?';
    params.push(limit);

    const messages = await env.DB.prepare(query).bind(...params).all();

    // Get unread count
    const unreadCount = await env.DB.prepare(
      'SELECT COUNT(*) as count FROM message WHERE recipient_id = ? AND is_read = 0'
    )
      .bind(user.userId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        messages: messages.results || [],
        count: messages.results?.length || 0,
        unread_count: unreadCount?.count || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Messages GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch messages',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/messages
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.recipient_id || !data.body) {
      return new Response(
        JSON.stringify({
          error: 'Recipient ID and body are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify recipient exists
    const recipient = await env.DB.prepare(
      'SELECT id FROM users WHERE id = ?'
    )
      .bind(data.recipient_id)
      .first();

    if (!recipient) {
      return new Response(
        JSON.stringify({
          error: 'Recipient not found',
        }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create message
    const result = await env.DB.prepare(
      `INSERT INTO message (
        sender_id, recipient_id, subject, body,
        message_type, priority, parent_message_id,
        property_id, task_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        user.userId,
        data.recipient_id,
        data.subject || null,
        data.body,
        data.message_type || 'direct',
        data.priority || 'normal',
        data.parent_message_id || null,
        data.property_id || null,
        data.task_id || null
      )
      .run();

    // Fetch created message
    const message = await env.DB.prepare(
      `SELECT
        m.id, m.sender_id, m.recipient_id, m.subject, m.body,
        m.message_type, m.priority, m.is_read, m.created_at,
        sender.first_name as sender_first_name,
        sender.last_name as sender_last_name,
        recipient.first_name as recipient_first_name,
        recipient.last_name as recipient_last_name
      FROM message m
      LEFT JOIN users sender ON m.sender_id = sender.id
      LEFT JOIN users recipient ON m.recipient_id = recipient.id
      WHERE m.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        message,
        message_text: 'Message sent successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Messages POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to send message',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
