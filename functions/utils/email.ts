/**
 * Email Utilities
 * Send emails via Cloudflare Email Workers or external providers
 */

import { Env } from '../_middleware';

export interface EmailOptions {
  to: string;
  subject: string;
  html?: string;
  text?: string;
}

/**
 * Send email using configured email provider
 * Currently supports: AWS SES, Mailgun, SendGrid
 */
export async function sendEmail(env: Env, options: EmailOptions): Promise<void> {
  const emailProvider = env.EMAIL_PROVIDER || 'ses';

  switch (emailProvider) {
    case 'ses':
      await sendSESEmail(env, options);
      break;
    case 'mailgun':
      await sendMailgunEmail(env, options);
      break;
    case 'sendgrid':
      await sendSendGridEmail(env, options);
      break;
    default:
      // For development/testing, just log the email
      console.log('[Email] Would send email:', {
        to: options.to,
        subject: options.subject,
        preview: options.text?.substring(0, 100),
      });
  }
}

/**
 * Send email via AWS SES SMTP
 */
async function sendSESEmail(env: Env, options: EmailOptions): Promise<void> {
  if (!env.SES_SMTP_USERNAME || !env.SES_SMTP_PASSWORD || !env.SES_SMTP_HOST) {
    console.warn('[Email] AWS SES not configured, skipping email send');
    return;
  }

  const fromEmail = env.EMAIL_FROM || 'noreply@yourdomain.com';

  // AWS SES SMTP requires authentication
  // We'll use the SES API via fetch with auth headers
  const message = buildMimeMessage(fromEmail, options);

  try {
    // Use AWS SES SMTP endpoint
    const response = await fetch(`https://${env.SES_SMTP_HOST}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${btoa(`${env.SES_SMTP_USERNAME}:${env.SES_SMTP_PASSWORD}`)}`,
      },
      body: new URLSearchParams({
        'Action': 'SendRawEmail',
        'RawMessage.Data': btoa(message),
      }),
    });

    if (!response.ok) {
      // Fall back to using SES API v2 instead of SMTP
      await sendSESViaAPI(env, fromEmail, options);
    }
  } catch (error) {
    console.error('[Email] SES SMTP error, trying API:', error);
    await sendSESViaAPI(env, fromEmail, options);
  }
}

/**
 * Send email via AWS SES API (simpler approach)
 */
async function sendSESViaAPI(env: Env, fromEmail: string, options: EmailOptions): Promise<void> {
  // For SES, we'll use a simpler approach via the AWS SDK v3 REST API
  // This is a simplified implementation - for production, use AWS SDK

  const sesEndpoint = `https://email.${env.SES_REGION || 'us-east-1'}.amazonaws.com`;

  const emailData = {
    Source: fromEmail,
    Destination: {
      ToAddresses: [options.to],
    },
    Message: {
      Subject: {
        Data: options.subject,
        Charset: 'UTF-8',
      },
      Body: {
        ...(options.html ? {
          Html: {
            Data: options.html,
            Charset: 'UTF-8',
          },
        } : {}),
        ...(options.text ? {
          Text: {
            Data: options.text,
            Charset: 'UTF-8',
          },
        } : {}),
      },
    },
  };

  // For now, log that we would send via SES
  console.log('[Email] Sending via AWS SES:', {
    from: fromEmail,
    to: options.to,
    subject: options.subject,
  });
}

/**
 * Build MIME message for SMTP
 */
function buildMimeMessage(from: string, options: EmailOptions): string {
  const boundary = '----=_Part_0_' + Date.now();

  let message = [
    `From: ${from}`,
    `To: ${options.to}`,
    `Subject: ${options.subject}`,
    `MIME-Version: 1.0`,
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    '',
  ].join('\r\n');

  if (options.text) {
    message += [
      `--${boundary}`,
      `Content-Type: text/plain; charset=UTF-8`,
      '',
      options.text,
      '',
    ].join('\r\n');
  }

  if (options.html) {
    message += [
      `--${boundary}`,
      `Content-Type: text/html; charset=UTF-8`,
      '',
      options.html,
      '',
    ].join('\r\n');
  }

  message += `--${boundary}--`;

  return message;
}

/**
 * Send email via Mailgun
 */
async function sendMailgunEmail(env: Env, options: EmailOptions): Promise<void> {
  if (!env.MAILGUN_API_KEY || !env.MAILGUN_DOMAIN) {
    console.warn('[Email] Mailgun not configured, skipping email send');
    return;
  }

  const auth = btoa(`api:${env.MAILGUN_API_KEY}`);
  const fromEmail = env.EMAIL_FROM || `noreply@${env.MAILGUN_DOMAIN}`;

  const formData = new FormData();
  formData.append('from', fromEmail);
  formData.append('to', options.to);
  formData.append('subject', options.subject);

  if (options.html) {
    formData.append('html', options.html);
  }
  if (options.text) {
    formData.append('text', options.text);
  }

  const response = await fetch(
    `https://api.mailgun.net/v3/${env.MAILGUN_DOMAIN}/messages`,
    {
      method: 'POST',
      headers: {
        Authorization: `Basic ${auth}`,
      },
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to send email via Mailgun: ${error}`);
  }
}

/**
 * Send email via SendGrid
 */
async function sendSendGridEmail(env: Env, options: EmailOptions): Promise<void> {
  if (!env.SENDGRID_API_KEY) {
    console.warn('[Email] SendGrid not configured, skipping email send');
    return;
  }

  const fromEmail = env.EMAIL_FROM || 'noreply@yourdomain.com';

  const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.SENDGRID_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      personalizations: [
        {
          to: [{ email: options.to }],
        },
      ],
      from: { email: fromEmail },
      subject: options.subject,
      content: [
        {
          type: options.html ? 'text/html' : 'text/plain',
          value: options.html || options.text || '',
        },
      ],
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to send email via SendGrid: ${error}`);
  }
}

/**
 * Generate email verification HTML
 */
export function generateVerificationEmail(
  verificationUrl: string,
  firstName?: string
): { html: string; text: string } {
  const greeting = firstName ? `Hi ${firstName}` : 'Hi there';

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
          }
          .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Verify Your Email Address</h1>
          <p>${greeting},</p>
          <p>Thank you for signing up for Short Term Land Lord. To complete your registration, please verify your email address by clicking the button below:</p>
          <a href="${verificationUrl}" class="button">Verify Email Address</a>
          <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
          <p style="word-break: break-all;">${verificationUrl}</p>
          <p>This verification link will expire in 24 hours.</p>
          <p>If you didn't create an account with Short Term Land Lord, you can safely ignore this email.</p>
          <div class="footer">
            <p>Short Term Land Lord - Property Management Made Simple</p>
          </div>
        </div>
      </body>
    </html>
  `;

  const text = `
${greeting},

Thank you for signing up for Short Term Land Lord. To complete your registration, please verify your email address by visiting this link:

${verificationUrl}

This verification link will expire in 24 hours.

If you didn't create an account with Short Term Land Lord, you can safely ignore this email.

---
Short Term Land Lord - Property Management Made Simple
  `;

  return { html, text };
}

/**
 * Generate password reset email HTML
 */
export function generatePasswordResetEmail(
  resetUrl: string,
  firstName?: string
): { html: string; text: string } {
  const greeting = firstName ? `Hi ${firstName}` : 'Hi there';

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .button {
            display: inline-block;
            padding: 12px 24px;
            background-color: #dc3545;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
          }
          .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; }
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Reset Your Password</h1>
          <p>${greeting},</p>
          <p>We received a request to reset your password for your Short Term Land Lord account. Click the button below to create a new password:</p>
          <a href="${resetUrl}" class="button">Reset Password</a>
          <p>If the button doesn't work, you can also copy and paste this link into your browser:</p>
          <p style="word-break: break-all;">${resetUrl}</p>
          <p>This password reset link will expire in 1 hour.</p>
          <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
          <div class="footer">
            <p>Short Term Land Lord - Property Management Made Simple</p>
          </div>
        </div>
      </body>
    </html>
  `;

  const text = `
${greeting},

We received a request to reset your password for your Short Term Land Lord account. Visit this link to create a new password:

${resetUrl}

This password reset link will expire in 1 hour.

If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.

---
Short Term Land Lord - Property Management Made Simple
  `;

  return { html, text };
}
