/**
 * Message Templates API
 * GET  /api/message-templates - List all templates
 * POST /api/message-templates - Create new template
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/message-templates
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    const category = url.searchParams.get('category');
    const active = url.searchParams.get('active');

    let query = 'SELECT * FROM message_template WHERE 1=1';
    const params: any[] = [];

    if (category) {
      query += ' AND category = ?';
      params.push(category);
    }

    if (active !== null && active !== undefined) {
      query += ' AND is_active = ?';
      params.push(active === 'true' ? 1 : 0);
    }

    query += ' ORDER BY category ASC, name ASC';

    const templates = await env.DB.prepare(query).bind(...params).all();

    return new Response(
      JSON.stringify({
        success: true,
        templates: templates.results || [],
        count: templates.results?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Message Templates GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch message templates',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/message-templates
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.name || !data.category || !data.body) {
      return new Response(
        JSON.stringify({
          error: 'Name, category, and body are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create template
    const result = await env.DB.prepare(
      `INSERT INTO message_template (
        name, category, subject, body, variables, channel, is_active, created_by_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.name,
        data.category,
        data.subject || null,
        data.body,
        data.variables ? JSON.stringify(data.variables) : null,
        data.channel || 'email',
        data.is_active !== undefined ? (data.is_active ? 1 : 0) : 1,
        user.userId
      )
      .run();

    // Fetch created template
    const template = await env.DB.prepare(
      'SELECT * FROM message_template WHERE id = ?'
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        template,
        message: 'Template created successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Message Templates POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create message template',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
