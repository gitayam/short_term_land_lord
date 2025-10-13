/**
 * Mark Message as Read
 * PUT /api/messages/[id]/read
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const messageId = params.id as string;

    // Verify message exists and user is recipient
    const message = await env.DB.prepare(
      'SELECT id FROM message WHERE id = ? AND recipient_id = ?'
    )
      .bind(messageId, user.userId)
      .first();

    if (!message) {
      return new Response(
        JSON.stringify({
          error: 'Message not found or access denied',
        }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Mark as read
    await env.DB.prepare(
      `UPDATE message
       SET is_read = 1, read_at = datetime('now')
       WHERE id = ?`
    )
      .bind(messageId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Message marked as read',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Message Read] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to mark message as read',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
