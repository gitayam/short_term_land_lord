/**
 * Complete Cleaning Session Endpoint
 * POST /api/cleaning/sessions/[id]/complete
 * Marks a cleaning session as completed with end time
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const sessionId = params.id;
    const { notes } = await request.json();

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

    // Verify user is the cleaner or has admin/owner permissions
    const canComplete =
      user.role === 'admin' ||
      session.cleaner_id === user.userId ||
      session.owner_id === user.userId;

    if (!canComplete) {
      return new Response(
        JSON.stringify({ error: 'Access denied' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if already completed
    if (session.status === 'completed') {
      return new Response(
        JSON.stringify({
          error: 'Cleaning session already completed',
          completed_at: session.end_time,
        }),
        {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Complete the session
    let updateQuery = `UPDATE cleaning_session
                       SET status = 'completed',
                           end_time = datetime('now'),
                           updated_at = datetime('now')`;
    const params: any[] = [];

    if (notes !== undefined && notes !== null) {
      updateQuery += ', notes = ?';
      params.push(notes);
    }

    updateQuery += ' WHERE id = ?';
    params.push(sessionId);

    await env.DB.prepare(updateQuery).bind(...params).run();

    // Fetch completed session
    const completedSession = await env.DB.prepare(
      `SELECT
        cs.id, cs.property_id, cs.cleaner_id, cs.start_time, cs.end_time,
        cs.status, cs.notes, cs.created_at, cs.updated_at,
        p.name as property_name, p.address as property_address,
        u.first_name as cleaner_first_name, u.last_name as cleaner_last_name
      FROM cleaning_session cs
      LEFT JOIN property p ON cs.property_id = p.id
      LEFT JOIN users u ON cs.cleaner_id = u.id
      WHERE cs.id = ?`
    )
      .bind(sessionId)
      .first();

    // Calculate duration
    if (completedSession) {
      const startTime = new Date(completedSession.start_time as string);
      const endTime = new Date(completedSession.end_time as string);
      const durationMinutes = Math.round(
        (endTime.getTime() - startTime.getTime()) / 1000 / 60
      );

      // Cache completion in KV for quick stats
      await env.KV.put(
        `cleaning-session:${sessionId}:stats`,
        JSON.stringify({
          duration_minutes: durationMinutes,
          completed_at: completedSession.end_time,
          cleaner_id: completedSession.cleaner_id,
          property_id: completedSession.property_id,
        }),
        { expirationTtl: 86400 * 90 } // 90 days
      );

      return new Response(
        JSON.stringify({
          success: true,
          session: completedSession,
          duration_minutes: durationMinutes,
          message: 'Cleaning session completed',
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Cleaning session completed',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Complete Cleaning Session] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to complete cleaning session',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
