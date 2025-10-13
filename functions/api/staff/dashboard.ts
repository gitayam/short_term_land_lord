/**
 * Staff Dashboard API
 * GET /api/staff/dashboard
 * Returns dashboard data for service staff (assigned properties, pending repairs, notifications)
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only service_staff and property_manager can access staff dashboard
    if (!['service_staff', 'property_manager', 'admin'].includes(user.role)) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Staff access required' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get assigned properties
    const assignedProperties = await env.DB.prepare(
      `SELECT
        pa.id as assignment_id,
        pa.role_type,
        pa.assigned_at,
        p.id as property_id,
        p.name,
        p.address,
        p.city,
        p.state
      FROM property_assignment pa
      JOIN property p ON pa.property_id = p.id
      WHERE pa.worker_id = ? AND pa.is_active = 1
      ORDER BY pa.assigned_at DESC`
    )
      .bind(user.userId)
      .all();

    // Get pending repair requests for assigned properties
    const pendingRepairs = await env.DB.prepare(
      `SELECT
        rr.*,
        p.name as property_name,
        p.address as property_address,
        u.first_name || ' ' || u.last_name as reported_by_name
      FROM repair_request rr
      JOIN property p ON rr.property_id = p.id
      JOIN users u ON rr.reported_by_id = u.id
      WHERE rr.property_id IN (
        SELECT property_id FROM property_assignment WHERE worker_id = ? AND is_active = 1
      )
      AND rr.status IN ('pending', 'approved')
      ORDER BY
        CASE rr.severity
          WHEN 'urgent' THEN 1
          WHEN 'high' THEN 2
          WHEN 'medium' THEN 3
          WHEN 'low' THEN 4
        END,
        rr.created_at DESC
      LIMIT 20`
    )
      .bind(user.userId)
      .all();

    // Get unread notifications
    const notifications = await env.DB.prepare(
      `SELECT *
       FROM staff_notification
       WHERE worker_id = ? AND is_read = 0
       ORDER BY created_at DESC
       LIMIT 10`
    )
      .bind(user.userId)
      .all();

    // Get recent work logs
    const recentWork = await env.DB.prepare(
      `SELECT
        wl.*,
        p.name as property_name,
        p.address as property_address
      FROM staff_work_log wl
      JOIN property p ON wl.property_id = p.id
      WHERE wl.worker_id = ?
      ORDER BY wl.start_time DESC
      LIMIT 10`
    )
      .bind(user.userId)
      .all();

    // Calculate stats
    const stats = {
      assigned_properties: assignedProperties.results?.length || 0,
      pending_repairs: pendingRepairs.results?.length || 0,
      unread_notifications: notifications.results?.length || 0,
      recent_work_logs: recentWork.results?.length || 0,
    };

    return new Response(
      JSON.stringify({
        success: true,
        stats,
        assigned_properties: assignedProperties.results || [],
        pending_repairs: pendingRepairs.results || [],
        notifications: notifications.results || [],
        recent_work: recentWork.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Staff Dashboard] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to load dashboard' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
