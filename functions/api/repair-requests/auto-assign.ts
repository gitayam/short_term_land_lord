/**
 * Automatic Worker Assignment API
 * POST /api/repair-requests/[id]/auto-assign
 * Automatically assigns repair request to best available worker based on:
 * - Worker specialty (role_type)
 * - Current workload
 * - Property assignment
 * - Repair severity
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';
import { createStaffNotification } from '../../utils/notifications';

interface WorkerScore {
  worker_id: number;
  worker_name: string;
  worker_email: string;
  role_type: string;
  score: number;
  reasons: string[];
  current_repairs: number;
}

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const repairRequestId = params.id as string;

    // Only admins and property_managers can auto-assign
    if (!['admin', 'property_manager'].includes(user.role)) {
      // Property owners can auto-assign for their own properties
      if (user.role === 'property_owner') {
        const repairRequest = await env.DB.prepare(
          `SELECT rr.*, p.owner_id
           FROM repair_request rr
           JOIN property p ON rr.property_id = p.id
           WHERE rr.id = ?`
        )
          .bind(repairRequestId)
          .first();

        if (!repairRequest || (repairRequest as any).owner_id !== user.userId) {
          return new Response(
            JSON.stringify({ error: 'Unauthorized' }),
            { status: 403, headers: { 'Content-Type': 'application/json' } }
          );
        }
      } else {
        return new Response(
          JSON.stringify({ error: 'Unauthorized' }),
          { status: 403, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // Get repair request details
    const repairRequest = await env.DB.prepare(
      `SELECT rr.*, p.name as property_name
       FROM repair_request rr
       JOIN property p ON rr.property_id = p.id
       WHERE rr.id = ?`
    )
      .bind(repairRequestId)
      .first();

    if (!repairRequest) {
      return new Response(
        JSON.stringify({ error: 'Repair request not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const rr = repairRequest as any;

    // Determine best role type based on repair title/description
    const repairText = `${rr.title} ${rr.description}`.toLowerCase();
    let preferredRoleType = 'general';

    if (repairText.includes('plumb') || repairText.includes('pipe') || repairText.includes('leak') || repairText.includes('drain')) {
      preferredRoleType = 'plumber';
    } else if (repairText.includes('electric') || repairText.includes('wire') || repairText.includes('outlet') || repairText.includes('light')) {
      preferredRoleType = 'electrician';
    } else if (repairText.includes('clean') || repairText.includes('dirt') || repairText.includes('stain')) {
      preferredRoleType = 'cleaner';
    } else if (repairText.includes('fix') || repairText.includes('broke') || repairText.includes('repair')) {
      preferredRoleType = 'handyman';
    }

    // Get all workers assigned to this property
    const workers = await env.DB.prepare(
      `SELECT
        pa.worker_id,
        pa.role_type,
        u.first_name || ' ' || u.last_name as worker_name,
        u.email as worker_email,
        u.is_active
      FROM property_assignment pa
      JOIN users u ON pa.worker_id = u.id
      WHERE pa.property_id = ? AND pa.is_active = 1 AND u.is_active = 1`
    )
      .bind(rr.property_id)
      .all();

    if (!workers.results || workers.results.length === 0) {
      return new Response(
        JSON.stringify({
          error: 'No workers assigned to this property',
          message: 'Please assign workers to this property before using auto-assignment'
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Score each worker
    const scoredWorkers: WorkerScore[] = await Promise.all(
      (workers.results as any[]).map(async (worker) => {
        const reasons: string[] = [];
        let score = 0;

        // +50 points for matching specialty
        if (worker.role_type === preferredRoleType) {
          score += 50;
          reasons.push(`Specialty match: ${preferredRoleType}`);
        } else if (worker.role_type === 'handyman' || worker.role_type === 'general') {
          score += 25;
          reasons.push('General maintenance capable');
        }

        // Get current workload (pending repairs)
        const workload = await env.DB.prepare(
          `SELECT COUNT(*) as count
           FROM repair_request rr
           JOIN property_assignment pa ON rr.property_id = pa.property_id
           WHERE pa.worker_id = ?
           AND rr.status IN ('pending', 'approved')
           AND pa.is_active = 1`
        )
          .bind(worker.worker_id)
          .first();

        const currentRepairs = (workload as any)?.count || 0;

        // Deduct points based on current workload
        if (currentRepairs === 0) {
          score += 30;
          reasons.push('No current assignments');
        } else if (currentRepairs <= 2) {
          score += 20;
          reasons.push(`Light workload (${currentRepairs} repairs)`);
        } else if (currentRepairs <= 5) {
          score += 10;
          reasons.push(`Moderate workload (${currentRepairs} repairs)`);
        } else {
          score -= 10;
          reasons.push(`Heavy workload (${currentRepairs} repairs)`);
        }

        // Bonus for urgent repairs (spread urgent work)
        if (rr.severity === 'urgent') {
          if (currentRepairs === 0) {
            score += 20;
            reasons.push('Urgent repair - available immediately');
          }
        }

        return {
          worker_id: worker.worker_id,
          worker_name: worker.worker_name,
          worker_email: worker.worker_email,
          role_type: worker.role_type,
          score,
          reasons,
          current_repairs: currentRepairs,
        };
      })
    );

    // Sort by score descending
    scoredWorkers.sort((a, b) => b.score - a.score);

    const bestWorker = scoredWorkers[0];

    // Update repair request to mark as approved (since we're assigning)
    await env.DB.prepare(
      `UPDATE repair_request
       SET status = 'approved',
           reviewed_by_id = ?,
           reviewed_at = datetime('now'),
           review_notes = ?
       WHERE id = ?`
    )
      .bind(
        user.userId,
        `Auto-assigned to ${bestWorker.worker_name} (${bestWorker.role_type})`,
        repairRequestId
      )
      .run();

    // Create notification for assigned worker
    await createStaffNotification(env, {
      workerId: bestWorker.worker_id,
      notificationType: 'repair_assigned',
      title: `Repair Assigned: ${rr.title}`,
      message: `You've been automatically assigned a ${rr.severity} priority repair at ${rr.property_name}`,
      link: `/app/repair-requests/${repairRequestId}`,
      relatedId: parseInt(repairRequestId),
      relatedType: 'repair_request',
    });

    return new Response(
      JSON.stringify({
        success: true,
        message: `Repair automatically assigned to ${bestWorker.worker_name}`,
        assigned_worker: {
          id: bestWorker.worker_id,
          name: bestWorker.worker_name,
          role_type: bestWorker.role_type,
          score: bestWorker.score,
          reasons: bestWorker.reasons,
          current_workload: bestWorker.current_repairs,
        },
        all_candidates: scoredWorkers,
        suggested_role: preferredRoleType,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Auto-Assign] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to auto-assign worker' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
