/**
 * Email Service Utility
 * Uses AWS SES for sending transactional emails
 * Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION in Cloudflare environment variables
 */

interface EmailParams {
  to: string;
  subject: string;
  html: string;
  replyTo?: string;
}

interface AWSCredentials {
  accessKeyId: string;
  secretAccessKey: string;
  region: string;
}

/**
 * Staff notification email templates
 */
export function staffRepairAssignedEmail(params: {
  workerName: string;
  repairTitle: string;
  severity: string;
  propertyName: string;
  propertyAddress: string;
  description: string;
  dashboardUrl: string;
}): { subject: string; html: string } {
  const severityColors = {
    urgent: '#EF4444',
    high: '#F97316',
    medium: '#EAB308',
    low: '#22C55E',
  };

  const color = severityColors[params.severity as keyof typeof severityColors] || '#6B7280';

  return {
    subject: `[${params.severity.toUpperCase()}] New Repair Assigned: ${params.repairTitle}`,
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9fafb; padding: 30px; }
            .severity-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; color: white; background: ${color}; }
            .property-info { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #2563EB; }
            .button { display: inline-block; padding: 14px 28px; background: #2563EB; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }
            .footer { text-align: center; padding: 20px; color: #6B7280; font-size: 14px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🔧 New Repair Assignment</h1>
            </div>
            <div class="content">
              <p>Hi ${params.workerName},</p>
              <p>You've been assigned a new repair request:</p>

              <div class="property-info">
                <h2>${params.repairTitle}</h2>
                <p><span class="severity-badge">${params.severity.toUpperCase()} PRIORITY</span></p>
                <p><strong>Property:</strong> ${params.propertyName}</p>
                <p><strong>Address:</strong> ${params.propertyAddress}</p>
                <p><strong>Description:</strong></p>
                <p>${params.description}</p>
              </div>

              <p>Please review this repair request and schedule a visit as soon as possible.</p>

              <a href="${params.dashboardUrl}" class="button">View in Dashboard →</a>
            </div>
            <div class="footer">
              <p>Short Term Land Lord - Staff Portal</p>
              <p>This is an automated notification. Please do not reply to this email.</p>
            </div>
          </div>
        </body>
      </html>
    `,
  };
}

export function staffPropertyAssignedEmail(params: {
  workerName: string;
  propertyName: string;
  propertyAddress: string;
  roleType: string;
  dashboardUrl: string;
}): { subject: string; html: string } {
  return {
    subject: `New Property Assignment: ${params.propertyName}`,
    html: `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9fafb; padding: 30px; }
            .property-card { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }
            .role-badge { display: inline-block; padding: 6px 12px; border-radius: 15px; background: #DBEAFE; color: #1E40AF; font-weight: bold; }
            .button { display: inline-block; padding: 14px 28px; background: #10B981; color: white; text-decoration: none; border-radius: 6px; font-weight: bold; margin: 20px 0; }
            .footer { text-align: center; padding: 20px; color: #6B7280; font-size: 14px; }
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>🏠 New Property Assignment</h1>
            </div>
            <div class="content">
              <p>Hi ${params.workerName},</p>
              <p>You've been assigned to a new property:</p>

              <div class="property-card">
                <h2>${params.propertyName}</h2>
                <p><strong>Address:</strong> ${params.propertyAddress}</p>
                <p><strong>Your Role:</strong> <span class="role-badge">${params.roleType}</span></p>
              </div>

              <p>You'll now receive notifications about maintenance and repair requests for this property.</p>

              <a href="${params.dashboardUrl}" class="button">View Property →</a>
            </div>
            <div class="footer">
              <p>Short Term Land Lord - Staff Portal</p>
              <p>This is an automated notification. Please do not reply to this email.</p>
            </div>
          </div>
        </body>
      </html>
    `,
  };
}

/**
 * Generate AWS Signature V4
 */
async function generateAwsSignature(
  credentials: AWSCredentials,
  method: string,
  url: string,
  headers: Record<string, string>,
  payload: string,
  service: string
): Promise<string> {
  const encoder = new TextEncoder();

  // Create canonical request
  const canonicalUri = new URL(url).pathname;
  const canonicalQueryString = '';
  const canonicalHeaders = Object.keys(headers)
    .sort()
    .map(key => `${key.toLowerCase()}:${headers[key].trim()}\n`)
    .join('');
  const signedHeaders = Object.keys(headers).sort().map(k => k.toLowerCase()).join(';');

  // Hash payload
  const payloadHash = await crypto.subtle.digest('SHA-256', encoder.encode(payload));
  const payloadHashHex = Array.from(new Uint8Array(payloadHash))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  const canonicalRequest = `${method}\n${canonicalUri}\n${canonicalQueryString}\n${canonicalHeaders}\n${signedHeaders}\n${payloadHashHex}`;

  // Create string to sign
  const date = new Date();
  const dateStamp = date.toISOString().slice(0, 10).replace(/-/g, '');
  const amzDate = date.toISOString().replace(/[:-]|\.\d{3}/g, '');
  const credentialScope = `${dateStamp}/${credentials.region}/${service}/aws4_request`;

  const canonicalRequestHash = await crypto.subtle.digest('SHA-256', encoder.encode(canonicalRequest));
  const canonicalRequestHashHex = Array.from(new Uint8Array(canonicalRequestHash))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  const stringToSign = `AWS4-HMAC-SHA256\n${amzDate}\n${credentialScope}\n${canonicalRequestHashHex}`;

  // Calculate signature
  const kDate = await hmacSha256(encoder.encode('AWS4' + credentials.secretAccessKey), encoder.encode(dateStamp));
  const kRegion = await hmacSha256(kDate, encoder.encode(credentials.region));
  const kService = await hmacSha256(kRegion, encoder.encode(service));
  const kSigning = await hmacSha256(kService, encoder.encode('aws4_request'));
  const signature = await hmacSha256(kSigning, encoder.encode(stringToSign));

  const signatureHex = Array.from(new Uint8Array(signature))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  return `AWS4-HMAC-SHA256 Credential=${credentials.accessKeyId}/${credentialScope}, SignedHeaders=${signedHeaders}, Signature=${signatureHex}`;
}

async function hmacSha256(key: ArrayBuffer | Uint8Array, data: Uint8Array): Promise<ArrayBuffer> {
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    key,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );
  return crypto.subtle.sign('HMAC', cryptoKey, data);
}

/**
 * Send email using AWS SES
 */
export async function sendEmail(params: EmailParams, credentials?: AWSCredentials, fromEmail?: string): Promise<boolean> {
  if (!credentials) {
    console.error('AWS credentials not configured');
    return false;
  }

  if (!fromEmail) {
    fromEmail = 'noreply@example.com'; // Update with your verified SES email
  }

  try {
    // Prepare SES SendEmail request
    const sesParams = {
      Destination: {
        ToAddresses: [params.to],
      },
      Message: {
        Body: {
          Html: {
            Charset: 'UTF-8',
            Data: params.html,
          },
        },
        Subject: {
          Charset: 'UTF-8',
          Data: params.subject,
        },
      },
      Source: fromEmail,
      ...(params.replyTo && { ReplyToAddresses: [params.replyTo] }),
    };

    const payload = JSON.stringify(sesParams);
    const url = `https://email.${credentials.region}.amazonaws.com/v2/email/outbound-emails`;

    const date = new Date();
    const amzDate = date.toISOString().replace(/[:-]|\.\d{3}/g, '');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Amz-Date': amzDate,
      'Host': `email.${credentials.region}.amazonaws.com`,
    };

    const authorization = await generateAwsSignature(
      credentials,
      'POST',
      url,
      headers,
      payload,
      'ses'
    );

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        ...headers,
        'Authorization': authorization,
      },
      body: payload,
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('SES email send failed:', error);
      return false;
    }

    return true;
  } catch (error) {
    console.error('Email send error:', error);
    return false;
  }
}

/**
 * Email template: New booking request notification (to owner)
 */
export function newBookingRequestEmail(data: {
  ownerName: string;
  propertyName: string;
  guestName: string;
  guestEmail: string;
  guestPhone: string | null;
  checkInDate: string;
  checkOutDate: string;
  numGuests: number;
  message: string | null;
  dashboardUrl: string;
}): { subject: string; html: string } {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const calculateNights = (checkIn: string, checkOut: string) => {
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const nights = calculateNights(data.checkInDate, data.checkOutDate);

  return {
    subject: `New Booking Request: ${data.propertyName}`,
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
          <h1 style="color: white; margin: 0; font-size: 28px;">🏠 New Booking Request</h1>
        </div>
        
        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
          <p style="font-size: 16px; margin-bottom: 20px;">Hi ${data.ownerName},</p>
          
          <p style="font-size: 16px; margin-bottom: 20px;">
            You have a new booking request for <strong>${data.propertyName}</strong>!
          </p>

          <div style="background: white; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #667eea; font-size: 20px;">Guest Information</h2>
            <p style="margin: 8px 0;"><strong>Name:</strong> ${data.guestName}</p>
            <p style="margin: 8px 0;"><strong>Email:</strong> <a href="mailto:${data.guestEmail}" style="color: #667eea;">${data.guestEmail}</a></p>
            ${data.guestPhone ? `<p style="margin: 8px 0;"><strong>Phone:</strong> ${data.guestPhone}</p>` : ''}
          </div>

          <div style="background: white; border-left: 4px solid #10b981; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #10b981; font-size: 20px;">Booking Details</h2>
            <p style="margin: 8px 0;"><strong>Check-in:</strong> ${formatDate(data.checkInDate)}</p>
            <p style="margin: 8px 0;"><strong>Check-out:</strong> ${formatDate(data.checkOutDate)}</p>
            <p style="margin: 8px 0;"><strong>Nights:</strong> ${nights}</p>
            <p style="margin: 8px 0;"><strong>Guests:</strong> ${data.numGuests}</p>
          </div>

          ${data.message ? `
          <div style="background: white; border-left: 4px solid #f59e0b; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #f59e0b; font-size: 20px;">Message from Guest</h2>
            <p style="margin: 0; font-style: italic;">"${data.message}"</p>
          </div>
          ` : ''}

          <div style="text-align: center; margin-top: 30px;">
            <a href="${data.dashboardUrl}" style="display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
              Review & Respond
            </a>
          </div>

          <p style="margin-top: 30px; font-size: 14px; color: #666; text-align: center;">
            Respond quickly to increase your booking conversion rate!
          </p>
        </div>

        <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
          <p>Fayetteville Rentals - Short-Term Rental Management</p>
          <p>This is an automated notification. Do not reply to this email.</p>
        </div>
      </body>
      </html>
    `,
  };
}

/**
 * Email template: Booking approved (to guest)
 */
export function bookingApprovedEmail(data: {
  guestName: string;
  propertyName: string;
  propertyAddress: string;
  checkInDate: string;
  checkOutDate: string;
  numGuests: number;
  ownerResponse?: string;
  propertyUrl?: string;
}): { subject: string; html: string } {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const calculateNights = (checkIn: string, checkOut: string) => {
    const start = new Date(checkIn);
    const end = new Date(checkOut);
    const diffTime = Math.abs(end.getTime() - start.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const nights = calculateNights(data.checkInDate, data.checkOutDate);

  return {
    subject: `✅ Booking Confirmed: ${data.propertyName}`,
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
          <h1 style="color: white; margin: 0; font-size: 28px;">✅ Booking Confirmed!</h1>
        </div>
        
        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
          <p style="font-size: 16px; margin-bottom: 20px;">Hi ${data.guestName},</p>
          
          <p style="font-size: 16px; margin-bottom: 20px;">
            Great news! Your booking request has been <strong>approved</strong>. We're excited to host you!
          </p>

          <div style="background: white; border-left: 4px solid #10b981; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #10b981; font-size: 20px;">Your Booking Details</h2>
            <p style="margin: 8px 0;"><strong>Property:</strong> ${data.propertyName}</p>
            <p style="margin: 8px 0;"><strong>Address:</strong> ${data.propertyAddress}</p>
            <p style="margin: 8px 0;"><strong>Check-in:</strong> ${formatDate(data.checkInDate)}</p>
            <p style="margin: 8px 0;"><strong>Check-out:</strong> ${formatDate(data.checkOutDate)}</p>
            <p style="margin: 8px 0;"><strong>Nights:</strong> ${nights}</p>
            <p style="margin: 8px 0;"><strong>Guests:</strong> ${data.numGuests}</p>
          </div>

          ${data.ownerResponse ? `
          <div style="background: white; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #667eea; font-size: 20px;">Message from Your Host</h2>
            <p style="margin: 0;">${data.ownerResponse}</p>
          </div>
          ` : ''}

          <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #f59e0b; font-size: 18px;">⚠️ Important Next Steps</h2>
            <ol style="margin: 10px 0; padding-left: 20px;">
              <li style="margin-bottom: 8px;">Complete your payment to secure your reservation</li>
              <li style="margin-bottom: 8px;">Check your email for check-in instructions</li>
              <li style="margin-bottom: 8px;">Contact us if you have any questions</li>
            </ol>
          </div>

          ${data.propertyUrl ? `
          <div style="text-align: center; margin-top: 30px;">
            <a href="${data.propertyUrl}" style="display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
              View Property Details
            </a>
          </div>
          ` : ''}

          <p style="margin-top: 30px; font-size: 14px; color: #666; text-align: center;">
            We look forward to welcoming you to Fayetteville, NC!
          </p>
        </div>

        <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
          <p>Fayetteville Rentals - Short-Term Rental Management</p>
          <p>Questions? Reply to this email or contact your host directly.</p>
        </div>
      </body>
      </html>
    `,
  };
}

/**
 * Email template: Booking rejected (to guest)
 */
export function bookingRejectedEmail(data: {
  guestName: string;
  propertyName: string;
  checkInDate: string;
  checkOutDate: string;
  ownerResponse?: string;
  searchUrl?: string;
}): { subject: string; html: string } {
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return {
    subject: `Booking Update: ${data.propertyName}`,
    html: `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
      </head>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
          <h1 style="color: white; margin: 0; font-size: 28px;">Booking Update</h1>
        </div>

        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
          <p style="font-size: 16px; margin-bottom: 20px;">Hi ${data.guestName},</p>

          <p style="font-size: 16px; margin-bottom: 20px;">
            Thank you for your interest in <strong>${data.propertyName}</strong>. Unfortunately, we're unable to accommodate your booking request for ${formatDate(data.checkInDate)} to ${formatDate(data.checkOutDate)}.
          </p>

          ${data.ownerResponse ? `
          <div style="background: white; border-left: 4px solid #667eea; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #667eea; font-size: 20px;">Message from Host</h2>
            <p style="margin: 0;">${data.ownerResponse}</p>
          </div>
          ` : ''}

          <div style="background: white; border-left: 4px solid #10b981; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
            <h2 style="margin-top: 0; color: #10b981; font-size: 18px;">We'd Still Love to Host You!</h2>
            <p style="margin: 0;">Consider checking our availability for different dates or exploring our other properties in Fayetteville, NC.</p>
          </div>

          ${data.searchUrl ? `
          <div style="text-align: center; margin-top: 30px;">
            <a href="${data.searchUrl}" style="display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
              Check Other Dates
            </a>
          </div>
          ` : ''}

          <p style="margin-top: 30px; font-size: 14px; color: #666; text-align: center;">
            Thank you for considering Fayetteville Rentals!
          </p>
        </div>

        <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
          <p>Fayetteville Rentals - Short-Term Rental Management</p>
          <p>Questions? Reply to this email or contact us directly.</p>
        </div>
      </body>
      </html>
    `,
  };
}

/**
 * Email template: Password reset (to user)
 */
export function generatePasswordResetEmail(
  resetUrl: string,
  firstName?: string
): { html: string; text: string } {
  const greeting = firstName ? `Hi ${firstName}` : 'Hi';

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">🔒 Reset Your Password</h1>
      </div>

      <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">${greeting},</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
          We received a request to reset your password for your Short Term Land Lord account.
        </p>

        <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
          <p style="margin: 0; font-size: 14px;">
            <strong>⏰ This link expires in 1 hour</strong> for security reasons.
          </p>
        </div>

        <div style="text-align: center; margin: 30px 0;">
          <a href="${resetUrl}" style="display: inline-block; background: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
            Reset Password
          </a>
        </div>

        <p style="font-size: 14px; color: #666; margin-top: 30px;">
          If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.
        </p>

        <div style="background: white; border-left: 4px solid #ef4444; padding: 20px; margin-top: 20px; border-radius: 5px;">
          <p style="margin: 0; font-size: 14px; color: #991b1b;">
            <strong>Security Tip:</strong> Never share your password reset link with anyone. Our team will never ask for your password.
          </p>
        </div>
      </div>

      <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
        <p>Short Term Land Lord - Property Management</p>
        <p>This is an automated security message. Do not reply to this email.</p>
      </div>
    </body>
    </html>
  `;

  const text = `
${greeting},

We received a request to reset your password for your Short Term Land Lord account.

Reset your password by clicking this link (expires in 1 hour):
${resetUrl}

If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.

Security Tip: Never share your password reset link with anyone. Our team will never ask for your password.

---
Short Term Land Lord - Property Management
This is an automated security message. Do not reply to this email.
  `.trim();

  return { html, text };
}

/**
 * Email template: Email verification (to user)
 */
export function generateVerificationEmail(
  verificationUrl: string,
  firstName?: string
): { html: string; text: string } {
  const greeting = firstName ? `Hi ${firstName}` : 'Hi';

  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
      <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">✉️ Verify Your Email</h1>
      </div>

      <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
        <p style="font-size: 16px; margin-bottom: 20px;">${greeting},</p>

        <p style="font-size: 16px; margin-bottom: 20px;">
          Thank you for creating an account with Short Term Land Lord! Please verify your email address to get started.
        </p>

        <div style="background: white; border-left: 4px solid #10b981; padding: 20px; margin-bottom: 20px; border-radius: 5px;">
          <h2 style="margin-top: 0; color: #10b981; font-size: 18px;">Why Verify?</h2>
          <ul style="margin: 10px 0; padding-left: 20px;">
            <li style="margin-bottom: 8px;">Secure your account</li>
            <li style="margin-bottom: 8px;">Receive important booking notifications</li>
            <li style="margin-bottom: 8px;">Get full access to all features</li>
          </ul>
        </div>

        <div style="text-align: center; margin: 30px 0;">
          <a href="${verificationUrl}" style="display: inline-block; background: #10b981; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 16px;">
            Verify Email Address
          </a>
        </div>

        <p style="font-size: 14px; color: #666; margin-top: 30px;">
          If you didn't create an account with Short Term Land Lord, you can safely ignore this email.
        </p>
      </div>

      <div style="text-align: center; padding: 20px; font-size: 12px; color: #999;">
        <p>Short Term Land Lord - Property Management</p>
        <p>Questions? Contact our support team.</p>
      </div>
    </body>
    </html>
  `;

  const text = `
${greeting},

Thank you for creating an account with Short Term Land Lord! Please verify your email address to get started.

Why Verify?
- Secure your account
- Receive important booking notifications
- Get full access to all features

Verify your email by clicking this link:
${verificationUrl}

If you didn't create an account with Short Term Land Lord, you can safely ignore this email.

---
Short Term Land Lord - Property Management
Questions? Contact our support team.
  `.trim();

  return { html, text };
}
