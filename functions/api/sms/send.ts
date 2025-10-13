/**
 * Send SMS API
 * POST /api/sms/send
 *
 * Requires Twilio credentials in environment:
 * - TWILIO_ACCOUNT_SID
 * - TWILIO_AUTH_TOKEN
 * - TWILIO_PHONE_NUMBER
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.recipient_phone || !data.message_body) {
      return new Response(
        JSON.stringify({
          error: 'Recipient phone and message body are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if Twilio is configured
    if (!env.TWILIO_ACCOUNT_SID || !env.TWILIO_AUTH_TOKEN || !env.TWILIO_PHONE_NUMBER) {
      console.warn('[SMS Send] Twilio not configured, logging message only');

      // Log to SMS table as 'pending' for manual processing
      const result = await env.DB.prepare(
        `INSERT INTO sms_log (
          recipient_phone, recipient_name, recipient_user_id,
          message_body, template_id, status, sent_by_id,
          property_id, booking_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
        .bind(
          data.recipient_phone,
          data.recipient_name || null,
          data.recipient_user_id || null,
          data.message_body,
          data.template_id || null,
          'pending',
          user.userId,
          data.property_id || null,
          data.booking_id || null
        )
        .run();

      return new Response(
        JSON.stringify({
          success: true,
          message: 'SMS queued for manual processing (Twilio not configured)',
          sms_log_id: result.meta.last_row_id,
          status: 'pending',
        }),
        {
          status: 202,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Send via Twilio
    const twilioUrl = `https://api.twilio.com/2010-04-01/Accounts/${env.TWILIO_ACCOUNT_SID}/Messages.json`;
    const twilioAuth = btoa(`${env.TWILIO_ACCOUNT_SID}:${env.TWILIO_AUTH_TOKEN}`);

    const twilioResponse = await fetch(twilioUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${twilioAuth}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        To: data.recipient_phone,
        From: env.TWILIO_PHONE_NUMBER,
        Body: data.message_body,
      }),
    });

    const twilioData = await twilioResponse.json();

    if (!twilioResponse.ok) {
      console.error('[SMS Send] Twilio error:', twilioData);

      // Log failed SMS
      await env.DB.prepare(
        `INSERT INTO sms_log (
          recipient_phone, recipient_name, recipient_user_id,
          message_body, template_id, status, error_message,
          sent_by_id, property_id, booking_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
        .bind(
          data.recipient_phone,
          data.recipient_name || null,
          data.recipient_user_id || null,
          data.message_body,
          data.template_id || null,
          'failed',
          twilioData.message || 'Unknown error',
          user.userId,
          data.property_id || null,
          data.booking_id || null
        )
        .run();

      return new Response(
        JSON.stringify({
          success: false,
          error: 'Failed to send SMS',
          message: twilioData.message || 'Unknown Twilio error',
        }),
        {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Log successful SMS
    const result = await env.DB.prepare(
      `INSERT INTO sms_log (
        recipient_phone, recipient_name, recipient_user_id,
        message_body, template_id, status, twilio_sid, twilio_status,
        segments, cost, sent_by_id, property_id, booking_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.recipient_phone,
        data.recipient_name || null,
        data.recipient_user_id || null,
        data.message_body,
        data.template_id || null,
        'sent',
        twilioData.sid,
        twilioData.status,
        twilioData.num_segments || 1,
        parseFloat(twilioData.price || '0'),
        user.userId,
        data.property_id || null,
        data.booking_id || null
      )
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'SMS sent successfully',
        sms_log_id: result.meta.last_row_id,
        twilio_sid: twilioData.sid,
        status: twilioData.status,
        segments: twilioData.num_segments,
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[SMS Send] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to send SMS',
        message: error.message,
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
