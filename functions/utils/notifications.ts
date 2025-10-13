/**
 * Notification Helper Functions
 * Create and send notifications to staff members
 */

import { Env } from '../_middleware';

export interface CreateNotificationParams {
  workerId: number;
  notificationType:
    | 'repair_assigned'
    | 'task_assigned'
    | 'property_assigned'
    | 'schedule_change'
    | 'repair_approved'
    | 'repair_rejected'
    | 'repair_requested';
  title: string;
  message: string;
  link?: string;
  relatedId?: number;
  relatedType?: 'repair_request' | 'task' | 'property';
}

/**
 * Create a staff notification
 */
export async function createStaffNotification(
  env: Env,
  params: CreateNotificationParams
): Promise<void> {
  const { workerId, notificationType, title, message, link, relatedId, relatedType } = params;

  try {
    await env.DB.prepare(
      `INSERT INTO staff_notification (
        worker_id, notification_type, title, message, link, related_id, related_type
      )
      VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        workerId,
        notificationType,
        title,
        message,
        link || null,
        relatedId || null,
        relatedType || null
      )
      .run();
  } catch (error) {
    console.error('[Create Staff Notification] Error:', error);
    // Don't throw - notification failure shouldn't break the main operation
  }
}

/**
 * Notify all workers assigned to a property
 */
export async function notifyPropertyWorkers(
  env: Env,
  propertyId: number,
  notificationType: CreateNotificationParams['notificationType'],
  title: string,
  message: string,
  link?: string,
  relatedId?: number,
  relatedType?: 'repair_request' | 'task' | 'property'
): Promise<void> {
  try {
    // Get all active workers for this property
    const workers = await env.DB.prepare(
      `SELECT worker_id FROM property_assignment
       WHERE property_id = ? AND is_active = 1`
    )
      .bind(propertyId)
      .all();

    if (!workers.results || workers.results.length === 0) {
      return;
    }

    // Create notification for each worker
    for (const worker of workers.results as any[]) {
      await createStaffNotification(env, {
        workerId: worker.worker_id,
        notificationType,
        title,
        message,
        link,
        relatedId,
        relatedType,
      });
    }
  } catch (error) {
    console.error('[Notify Property Workers] Error:', error);
  }
}

/**
 * Send email notification to staff (if configured)
 */
export async function emailStaffNotification(
  env: Env,
  notificationId: number
): Promise<void> {
  // TODO: Implement email sending via Resend API
  // This would:
  // 1. Get notification details
  // 2. Get worker email
  // 3. Send email via Resend
  // 4. Mark notification as emailed
  console.log(`[Email Staff Notification] TODO: Send email for notification ${notificationId}`);
}
