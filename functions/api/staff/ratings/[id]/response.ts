/**
 * Staff Rating Response API
 * POST /api/staff/ratings/[id]/response - Worker responds to a rating
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const ratingId = params.id as string;

    // Only service_staff can respond to ratings
    if (user.role !== 'service_staff') {
      return new Response(
        JSON.stringify({ error: 'Only staff can respond to ratings' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data = await request.json();
    const { response_text } = data as any;

    if (!response_text) {
      return new Response(
        JSON.stringify({ error: 'response_text is required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify rating exists and belongs to this worker
    const rating = await env.DB.prepare(
      `SELECT id, worker_id, rated_by_id FROM staff_rating WHERE id = ?`
    )
      .bind(ratingId)
      .first();

    if (!rating) {
      return new Response(
        JSON.stringify({ error: 'Rating not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if ((rating as any).worker_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'You can only respond to your own ratings' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Check if response already exists
    const existingResponse = await env.DB.prepare(
      `SELECT id FROM staff_rating_response WHERE rating_id = ?`
    )
      .bind(ratingId)
      .first();

    if (existingResponse) {
      // Update existing response
      await env.DB.prepare(
        `UPDATE staff_rating_response
         SET response_text = ?,
             created_at = datetime('now')
         WHERE rating_id = ?`
      )
        .bind(response_text, ratingId)
        .run();
    } else {
      // Create new response
      await env.DB.prepare(
        `INSERT INTO staff_rating_response (
          rating_id,
          worker_id,
          response_text
        ) VALUES (?, ?, ?)`
      )
        .bind(ratingId, user.userId, response_text)
        .run();
    }

    // Notify the person who left the rating (if not anonymous)
    const ratedById = (rating as any).rated_by_id;
    if (ratedById) {
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
          ratedById,
          'rating_response',
          'Worker Responded to Your Rating',
          'A worker has responded to your rating',
          `/app/workers/${user.userId}`
        )
        .run();
    }

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Response submitted successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Rating Response] Post error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to submit response' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
