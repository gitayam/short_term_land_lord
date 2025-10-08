/**
 * Individual Cleaning Session Endpoint
 * GET /api/cleaning/sessions/[id] - Get session details
 * PUT /api/cleaning/sessions/[id] - Update session
 * DELETE /api/cleaning/sessions/[id] - Delete session
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;

    if (!sessionId) {
      return new Response(
        JSON.stringify({ error: 'Session ID is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get session with property details
    const session = await env.DB.prepare(
      `SELECT
        cs.id, cs.property_id, cs.cleaner_id, cs.start_time, cs.end_time,
        cs.status, cs.notes, cs.created_at, cs.updated_at,
        p.name as property_name, p.address as property_address, p.owner_id,
        u.first_name as cleaner_first_name, u.last_name as cleaner_last_name,
        u.email as cleaner_email
      FROM cleaning_session cs
      LEFT JOIN property p ON cs.property_id = p.id
      LEFT JOIN users u ON cs.cleaner_id = u.id
      WHERE cs.id = ?`
    )
      .bind(sessionId)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({ error: 'Cleaning session not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify access permissions
    const hasAccess =
      user.role === 'admin' ||
      session.cleaner_id === user.userId ||
      session.owner_id === user.userId;

    if (!hasAccess) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get media files from KV
    const mediaKey = `cleaning-session:${sessionId}:media`;
    const media = await env.KV.get(mediaKey, { type: 'json' });

    return new Response(
      JSON.stringify({
        success: true,
        session,
        media: media || [],
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Session] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to fetch cleaning session',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;
    const { notes, status } = await request.json();

    if (!sessionId) {
      return new Response(
        JSON.stringify({ error: 'Session ID is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get session
    const session = await env.DB.prepare(
      'SELECT cs.*, p.owner_id FROM cleaning_session cs LEFT JOIN property p ON cs.property_id = p.id WHERE cs.id = ?'
    )
      .bind(sessionId)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({ error: 'Cleaning session not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify permissions
    const canEdit =
      user.role === 'admin' ||
      session.cleaner_id === user.userId ||
      session.owner_id === user.userId;

    if (!canEdit) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate status if provided
    if (status && !['in_progress', 'completed', 'cancelled'].includes(status)) {
      return new Response(
        JSON.stringify({ error: 'Invalid status value' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Build update query
    let updateQuery = 'UPDATE cleaning_session SET updated_at = datetime(\'now\')';
    const params: any[] = [];

    if (notes !== undefined) {
      updateQuery += ', notes = ?';
      params.push(notes);
    }

    if (status !== undefined) {
      updateQuery += ', status = ?';
      params.push(status);
    }

    updateQuery += ' WHERE id = ?';
    params.push(sessionId);

    await env.DB.prepare(updateQuery).bind(...params).run();

    // Fetch updated session
    const updatedSession = await env.DB.prepare(
      `SELECT
        cs.id, cs.property_id, cs.cleaner_id, cs.start_time, cs.end_time,
        cs.status, cs.notes, cs.created_at, cs.updated_at,
        p.name as property_name, p.address as property_address
      FROM cleaning_session cs
      LEFT JOIN property p ON cs.property_id = p.id
      WHERE cs.id = ?`
    )
      .bind(sessionId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        session: updatedSession,
        message: 'Cleaning session updated',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Session] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to update cleaning session',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;

    if (!sessionId) {
      return new Response(
        JSON.stringify({ error: 'Session ID is required' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Get session
    const session = await env.DB.prepare(
      'SELECT cs.*, p.owner_id FROM cleaning_session cs LEFT JOIN property p ON cs.property_id = p.id WHERE cs.id = ?'
    )
      .bind(sessionId)
      .first();

    if (!session) {
      return new Response(
        JSON.stringify({ error: 'Cleaning session not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Only admin or property owner can delete
    const canDelete = user.role === 'admin' || session.owner_id === user.userId;

    if (!canDelete) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete session
    await env.DB.prepare('DELETE FROM cleaning_session WHERE id = ?')
      .bind(sessionId)
      .run();

    // Clean up media metadata from KV
    await env.KV.delete(`cleaning-session:${sessionId}:media`);

    // Note: R2 files are not deleted for data retention
    // Implement cleanup job if needed

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Cleaning session deleted',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Cleaning Session] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete cleaning session',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
