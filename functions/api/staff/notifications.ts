/**
 * Staff Notifications API
 * GET /api/staff/notifications - List notifications for current staff member
 * PATCH /api/staff/notifications - Mark notifications as read
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/staff/notifications
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only staff can access notifications
    if (!['service_staff', 'property_manager', 'admin'].includes(user.role)) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Staff access required' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const url = new URL(request.url);
    const unreadOnly = url.searchParams.get('unread_only') === 'true';
    const limit = parseInt(url.searchParams.get('limit') || '50');

    let query = `
      SELECT *
      FROM staff_notification
      WHERE worker_id = ?
    `;

    if (unreadOnly) {
      query += ' AND is_read = 0';
    }

    query += ' ORDER BY created_at DESC LIMIT ?';

    const notifications = await env.DB.prepare(query)
      .bind(user.userId, limit)
      .all();

    return new Response(
      JSON.stringify({
        success: true,
        notifications: notifications.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Staff Notifications GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch notifications' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PATCH /api/staff/notifications - Mark as read
export const onRequestPatch: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only staff can update notifications
    if (!['service_staff', 'property_manager', 'admin'].includes(user.role)) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Staff access required' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data = await request.json();
    const { notification_ids, mark_all_read } = data;

    if (mark_all_read) {
      // Mark all notifications as read for this worker
      await env.DB.prepare(
        'UPDATE staff_notification SET is_read = 1 WHERE worker_id = ? AND is_read = 0'
      )
        .bind(user.userId)
        .run();

      return new Response(
        JSON.stringify({
          success: true,
          message: 'All notifications marked as read',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if (!notification_ids || !Array.isArray(notification_ids)) {
      return new Response(
        JSON.stringify({ error: 'notification_ids array or mark_all_read flag required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Mark specific notifications as read (only if they belong to this worker)
    const placeholders = notification_ids.map(() => '?').join(',');
    await env.DB.prepare(
      `UPDATE staff_notification
       SET is_read = 1
       WHERE id IN (${placeholders})
       AND worker_id = ?`
    )
      .bind(...notification_ids, user.userId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Notifications marked as read',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Staff Notifications PATCH] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to update notifications' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
