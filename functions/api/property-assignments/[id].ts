/**
 * Property Assignment Detail API
 * DELETE /api/property-assignments/[id] - Remove property assignment
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// DELETE /api/property-assignments/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const assignmentId = params.id as string;

    // Only admins and property_managers can delete assignments
    if (user.role !== 'admin' && user.role !== 'property_manager') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized - Admin or Property Manager access required' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify assignment exists
    const assignment = await env.DB.prepare(
      'SELECT id FROM property_assignment WHERE id = ?'
    )
      .bind(assignmentId)
      .first();

    if (!assignment) {
      return new Response(
        JSON.stringify({ error: 'Assignment not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete assignment
    await env.DB.prepare('DELETE FROM property_assignment WHERE id = ?')
      .bind(assignmentId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Property assignment removed successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Property Assignment DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to remove property assignment',
      }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
