# AWS SES Email Setup Guide

This guide walks you through setting up AWS Simple Email Service (SES) for sending transactional emails from your Short Term Landlord application.

## Why AWS SES?

- **Cost-effective**: $0.10 per 1,000 emails
- **Reliable**: 99.9% uptime SLA
- **Scalable**: Send millions of emails
- **Secure**: Built-in authentication and encryption
- **API-based**: No SMTP configuration needed

## Step 1: Create AWS Account

1. Go to [AWS Console](https://console.aws.amazon.com)
2. Sign up for a new account or log in
3. Navigate to **SES (Simple Email Service)**

## Step 2: Verify Your Email Domain

### Option A: Verify Single Email Address (Quick Start)

1. In SES Console, go to **Email Addresses** → **Verify a New Email Address**
2. Enter your email (e.g., `noreply@yourdomain.com`)
3. Check your inbox and click the verification link
4. **Note**: This allows sending FROM this address, but only TO verified addresses (sandbox mode)

### Option B: Verify Entire Domain (Recommended for Production)

1. In SES Console, go to **Domains** → **Verify a New Domain**
2. Enter your domain (e.g., `yourdomain.com`)
3. AWS will provide DNS records (TXT, CNAME, DKIM)
4. Add these records to your DNS provider
5. Wait for verification (usually 10-30 minutes)
6. **Benefit**: Can send from any address @yourdomain.com

## Step 3: Request Production Access

By default, SES starts in **Sandbox Mode** with limitations:
- Can only send TO verified email addresses
- Limited to 200 emails per day
- Max 1 email per second

To remove these limits:

1. In SES Console, click **Request Production Access**
2. Fill out the form:
   - **Mail Type**: Transactional
   - **Website URL**: Your property website
   - **Use Case Description**:
     ```
     We are building a short-term rental property management system.
     We need to send transactional emails to guests including:
     - Booking confirmations
     - Booking approvals/rejections
     - Check-in instructions
     - Pre-arrival reminders

     Expected volume: ~50-200 emails per day initially.
     We will implement proper bounce and complaint handling.
     ```
3. Submit and wait for approval (usually 24-48 hours)

## Step 4: Create IAM User for API Access

1. Go to **IAM** in AWS Console
2. Click **Users** → **Add User**
3. User name: `ses-api-user`
4. Access type: **Programmatic access** (for API)
5. Permissions: Attach policy **AmazonSESFullAccess**
   - Or create custom policy with only `ses:SendEmail` permission
6. Click through and **Download credentials CSV**
7. **Important**: Save the Access Key ID and Secret Access Key securely

### Example Custom Policy (Minimum Permissions):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ],
      "Resource": "*"
    }
  ]
}
```

## Step 5: Configure Cloudflare Pages Environment Variables

Add these to **Cloudflare Dashboard → Pages → short-term-landlord → Settings → Environment Variables**:

### Production and Preview Environments:

```bash
# AWS SES Credentials
AWS_ACCESS_KEY_ID=AKIA...           # From IAM user
AWS_SECRET_ACCESS_KEY=wJalrXUtn...  # From IAM user
AWS_REGION=us-east-1                # SES region (where you verified domain)
AWS_SES_FROM_EMAIL=noreply@yourdomain.com  # Verified sender email
```

### Recommended Regions:
- **us-east-1** (N. Virginia) - Most features, lowest cost
- **us-west-2** (Oregon) - West coast
- **eu-west-1** (Ireland) - Europe

## Step 6: Test Email Sending

### Manual Test via AWS Console:

1. Go to SES → **Email Addresses**
2. Select your verified email
3. Click **Send a Test Email**
4. Send to yourself to verify it works

### Test via Application:

1. Deploy your code with environment variables
2. Trigger a booking approval/rejection
3. Check recipient inbox and AWS SES **Sending Statistics**

## Step 7: Monitor and Handle Bounces

### Set Up SNS Notifications:

1. Go to SES → **Email Addresses** or **Domains**
2. Click your verified email/domain
3. Set up **SNS Topic** for:
   - Bounces
   - Complaints
4. Subscribe to SNS topic via email or Lambda function

### Best Practices:

- **Monitor bounce rate**: Keep below 5%
- **Remove bounced emails**: Don't send to invalid addresses
- **Handle complaints**: Unsubscribe immediately
- **Check reputation**: AWS dashboard shows reputation metrics

## Troubleshooting

### Issue: Emails Not Sending

**Check:**
1. Environment variables are set correctly in Cloudflare
2. AWS Access Key has `ses:SendEmail` permission
3. FROM address is verified in SES
4. TO address is verified (if in sandbox mode)
5. Check Cloudflare Functions logs for errors

### Issue: "Email address is not verified"

**Solution:**
- If in sandbox mode, verify the recipient's email in SES Console
- OR request production access to send to any email

### Issue: "Daily sending quota exceeded"

**Solution:**
- Request production access (default: 200/day in sandbox)
- Check SES **Sending Statistics** for current quota

### Issue: High bounce rate warning

**Solution:**
- Validate email addresses before sending
- Remove bounced addresses from your list
- Use double opt-in for new subscribers

## Cost Estimate

**AWS SES Pricing** (as of 2024):
- First 62,000 emails/month: **$0** (with EC2/Lambda)
- Without EC2/Lambda: **$0.10 per 1,000 emails**

**Example Usage:**
- 50 bookings/day × 2 emails each (guest + owner) = 100 emails/day
- 100 × 30 days = 3,000 emails/month
- Cost: **$0.30/month** or FREE with EC2

## Security Best Practices

1. **Rotate credentials** every 90 days
2. **Use IAM roles** instead of access keys when possible
3. **Enable MFA** on AWS root account
4. **Monitor CloudTrail** for SES API calls
5. **Set up alerts** for unusual sending patterns
6. **Use separate IAM users** for different environments (dev/prod)

## Email Templates

The application includes beautiful HTML email templates for:

- ✅ **Booking Request** - Notifies owner of new booking
- ✅ **Booking Approved** - Confirms booking to guest
- ✅ **Booking Rejected** - Politely declines guest booking
- ✅ **Password Reset** - Secure password reset link
- ✅ **Email Verification** - Verify user email address

Templates are in: `/functions/utils/email.ts`

## Additional Resources

- [AWS SES Documentation](https://docs.aws.amazon.com/ses/)
- [SES Pricing](https://aws.amazon.com/ses/pricing/)
- [SES Best Practices](https://docs.aws.amazon.com/ses/latest/DeveloperGuide/best-practices.html)
- [SES FAQs](https://aws.amazon.com/ses/faqs/)

## Support

If you encounter issues:
1. Check Cloudflare Functions logs
2. Check AWS SES Sending Statistics
3. Review AWS CloudWatch logs
4. Contact AWS Support (if business/enterprise plan)
