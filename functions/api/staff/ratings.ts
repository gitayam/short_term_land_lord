/**
 * Staff Ratings API
 * POST /api/staff/ratings - Submit a rating for staff
 * GET /api/staff/ratings?worker_id=X - Get ratings for a worker
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);
    const workerId = url.searchParams.get('worker_id');

    if (!workerId) {
      return new Response(JSON.stringify({ error: 'worker_id parameter required' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // Get ratings for worker
    const ratings = await env.DB.prepare(
      `SELECT
        sr.*,
        u.first_name || ' ' || u.last_name as worker_name,
        CASE
          WHEN sr.is_anonymous = 1 THEN 'Anonymous'
          ELSE rb.first_name || ' ' || rb.last_name
        END as rated_by_name,
        p.name as property_name,
        rr.title as repair_title
      FROM staff_rating sr
      JOIN users u ON sr.worker_id = u.id
      LEFT JOIN users rb ON sr.rated_by_id = rb.id
      LEFT JOIN property p ON sr.property_id = p.id
      LEFT JOIN repair_request rr ON sr.repair_request_id = rr.id
      WHERE sr.worker_id = ?
      ORDER BY sr.created_at DESC`
    )
      .bind(workerId)
      .all();

    // Calculate average ratings
    const avgRatings = await env.DB.prepare(
      `SELECT
        COUNT(*) as total_ratings,
        ROUND(AVG(rating), 2) as avg_overall,
        ROUND(AVG(quality_rating), 2) as avg_quality,
        ROUND(AVG(timeliness_rating), 2) as avg_timeliness,
        ROUND(AVG(communication_rating), 2) as avg_communication,
        ROUND(AVG(professionalism_rating), 2) as avg_professionalism
      FROM staff_rating
      WHERE worker_id = ?`
    )
      .bind(workerId)
      .first();

    // Get rating distribution (1-5 stars)
    const distribution = await env.DB.prepare(
      `SELECT
        rating,
        COUNT(*) as count
      FROM staff_rating
      WHERE worker_id = ?
      GROUP BY rating
      ORDER BY rating DESC`
    )
      .bind(workerId)
      .all();

    return new Response(
      JSON.stringify({
        ratings: ratings.results,
        averages: avgRatings,
        distribution: distribution.results,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Ratings] Get error:', error);
    return new Response(JSON.stringify({ error: error.message || 'Failed to fetch ratings' }), {
      status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);

    // Only property owners, managers, and admins can submit ratings
    if (!['property_owner', 'property_manager', 'admin'].includes(user.role)) {
      return new Response(JSON.stringify({ error: 'Unauthorized' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    const data = await request.json();
    const {
      worker_id,
      property_id,
      work_log_id,
      repair_request_id,
      rating,
      quality_rating,
      timeliness_rating,
      communication_rating,
      professionalism_rating,
      comment,
      is_anonymous,
    } = data as any;

    // Validate required fields
    if (!worker_id || !rating) {
      return new Response(
        JSON.stringify({ error: 'worker_id and rating are required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Validate rating range
    if (rating < 1 || rating > 5) {
      return new Response(
        JSON.stringify({ error: 'rating must be between 1 and 5' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify worker exists and is service_staff
    const worker = await env.DB.prepare(
      `SELECT id, role FROM users WHERE id = ?`
    )
      .bind(worker_id)
      .first();

    if (!worker || (worker as any).role !== 'service_staff') {
      return new Response(
        JSON.stringify({ error: 'Invalid worker ID' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // For property owners, verify they own the property
    if (user.role === 'property_owner' && property_id) {
      const property = await env.DB.prepare(
        `SELECT id FROM property WHERE id = ? AND owner_id = ?`
      )
        .bind(property_id, user.userId)
        .first();

      if (!property) {
        return new Response(
          JSON.stringify({ error: 'You can only rate workers on your own properties' }),
          { status: 403, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // Insert rating
    const result = await env.DB.prepare(
      `INSERT INTO staff_rating (
        worker_id,
        rated_by_id,
        property_id,
        work_log_id,
        repair_request_id,
        rating,
        quality_rating,
        timeliness_rating,
        communication_rating,
        professionalism_rating,
        comment,
        is_anonymous
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      RETURNING id`
    )
      .bind(
        worker_id,
        user.userId,
        property_id || null,
        work_log_id || null,
        repair_request_id || null,
        rating,
        quality_rating || null,
        timeliness_rating || null,
        communication_rating || null,
        professionalism_rating || null,
        comment || null,
        is_anonymous ? 1 : 0
      )
      .first();

    // Create notification for worker
    await env.DB.prepare(
      `INSERT INTO staff_notification (
        worker_id,
        notification_type,
        title,
        message,
        link
      ) VALUES (?, ?, ?, ?, ?)`
    )
      .bind(
        worker_id,
        'rating_received',
        'New Rating Received',
        `You received a ${rating}-star rating${comment ? ' with a comment' : ''}`,
        '/app/staff'
      )
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Rating submitted successfully',
        rating_id: (result as any)?.id,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Ratings] Post error:', error);
    return new Response(JSON.stringify({ error: error.message || 'Failed to submit rating' }), {
      status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
      headers: { 'Content-Type': 'application/json' },
    });
  }
};
