# Signal Bridge Integration Setup Guide

## Overview

This guide explains how to complete the Signal verification workflow after the identifier resolution succeeds. The Signal bridge successfully resolved your phone number (+12247253276) to UUID (770b19f5-389e-444e-8976-551a52136cf6), but the direct messaging step was missing.

## What Was Missing

After the Signal bridge resolves an identifier, it needs to:
1. ✅ **Resolved**: `resolve-identifier +12247253276` → `770b19f5-389e-444e-8976-551a52136cf6`
2. ❌ **Missing**: Create or find existing DM room
3. ❌ **Missing**: Send preparatory message for encryption
4. ❌ **Missing**: Send actual verification message

## Implementation Added

### 1. Signal Bridge Service (`app/utils/signal_bridge.py`)

```python
class SignalBridgeService:
    async def handle_identifier_resolved(self, phone_number, signal_uuid, user_data):
        """Complete workflow after identifier resolution"""
        # Find user in database
        # Check for existing DM room  
        # Create new room if needed using signalbot commands
        # Send preparatory + verification messages
        
    async def create_private_message_room(self, signal_uuid, display_name):
        """Use signalbot command: !signal pm {uuid}"""
        signalbot_command = f"!signal pm {signal_uuid}"
        await self.send_bridge_command(signalbot_command)
        
    async def send_verification_message(self, room_id, user, signal_uuid):
        """Send preparatory message + verification"""
        # Step 1: Send "🔐 Securing message..." 
        # Step 2: Wait for Element encryption setup
        # Step 3: Send actual verification message
```

### 2. Webhook Handler (`/messages/signal-webhook`)

```python
@bp.route('/signal-webhook', methods=['POST'])
def signal_webhook():
    """Handle Signal bridge events"""
    if event_type == 'identifier_resolved':
        phone_number = data.get('phone_number')  # +12247253276
        signal_uuid = data.get('signal_uuid')    # 770b19f5-389e-444e-8976-551a52136cf6
        
        # Trigger the missing direct messaging workflow
        await handle_signal_resolution(phone_number, signal_uuid, display_name)
```

## Configuration Required

Add to your `.env` file:

```bash
# Signal Bridge Configuration
SIGNAL_BRIDGE_ENABLED=true
SIGNAL_BRIDGE_ROOM_ID=!your_signal_bridge_room:matrix.org
MATRIX_BOT_USER_ID=@your_bot:matrix.org
MATRIX_ACCESS_TOKEN=your_matrix_access_token
MATRIX_HOMESERVER=matrix.org
SIGNAL_WEBHOOK_URL=https://your-domain.com/messages/signal-webhook
```

## Testing the Fix

### Manual Testing

```bash
# Test the resolution handling directly
python test_signal_resolution.py
```

### Webhook Testing

```bash
# Send a test webhook payload
curl -X POST https://your-domain.com/messages/signal-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "identifier_resolved",
    "phone_number": "+12247253276", 
    "signal_uuid": "770b19f5-389e-444e-8976-551a52136cf6",
    "display_name": "Sac"
  }'
```

## Integration with Existing Signal Bridge

### Option 1: Event-Driven (Recommended)

Set up your Signal bridge to send webhooks when identifier resolution completes:

```python
# In your Signal bridge bot
async def on_identifier_resolved(phone_number, signal_uuid, display_name):
    webhook_data = {
        "type": "identifier_resolved",
        "phone_number": phone_number,
        "signal_uuid": signal_uuid, 
        "display_name": display_name,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Send to Flask app webhook
    await send_webhook(FLASK_WEBHOOK_URL, webhook_data)
```

### Option 2: Direct Integration

Integrate the `SignalBridgeService` directly into your Streamlit Signal bridge:

```python
# In your Streamlit Signal bridge
from your_flask_app.app.utils.signal_bridge import SignalBridgeService

signal_service = SignalBridgeService()

async def handle_resolve_result(phone_number, signal_uuid, display_name):
    # After successful resolution in Streamlit
    success = await signal_service.handle_identifier_resolved(
        phone_number, signal_uuid, {"display_name": display_name}
    )
    
    if success:
        st.success(f"✅ Direct message sent to {display_name}")
    else:
        st.error("❌ Failed to send direct message")
```

## Expected Workflow

1. **User triggers verification**: In Signal bridge room
   ```
   resolve-identifier +12247253276
   ```

2. **Bridge resolves identifier**: 
   ```
   IrregularChat Bot
   resolve-identifier +12247253276
   signal bridge bot  
   Found 770b19f5-389e-444e-8976-551a52136cf6 / Sac
   ```

3. **Bridge triggers webhook** (NEW):
   ```
   POST /messages/signal-webhook
   {
     "type": "identifier_resolved",
     "phone_number": "+12247253276",
     "signal_uuid": "770b19f5-389e-444e-8976-551a52136cf6", 
     "display_name": "Sac"
   }
   ```

4. **Flask app handles resolution** (NEW):
   - Find user in database by phone number
   - Check for existing DM room with Signal UUID
   - Create new room: `!signal pm 770b19f5-389e-444e-8976-551a52136cf6`
   - Send preparatory message: "🔐 Securing message..."
   - Wait 3 seconds for Element encryption
   - Send verification message with user details

5. **User receives Signal message** (NEW):
   ```
   🔐 Securing message...
   
   ✅ Signal Verification for Sac
   
   Your phone number has been successfully verified for the Short Term Landlord Property Management System.
   
   📱 Phone: +12247253276
   📧 Email: user@example.com  
   🏢 Role: service_staff
   
   You can now:
   • Receive SMS notifications for tasks and updates
   • Reply to this message for direct communication
   • Use 'HELP' for available commands
   
   Welcome to the system! 🎉
   ```

## Signalbot Commands Reference

Based on your description, these commands should work in your Signal bridge:

```bash
# Create direct message room
!signal pm <signal_uuid>

# Alternative syntax (if supported)
!signal dm <signal_uuid>

# Send message to existing room
!signal send <room_id> <message>
```

## Troubleshooting

### Common Issues

1. **"Bridge room ID not configured"**
   - Set `SIGNAL_BRIDGE_ROOM_ID` in your environment
   - Format: `!roomid:matrix.org`

2. **"Matrix client not authenticated"**  
   - Verify `MATRIX_ACCESS_TOKEN` is valid
   - Check bot has proper permissions

3. **"User not found for phone number"**
   - Ensure user exists in database with correct phone format
   - Check phone number formatting (E.164 format)

4. **"Failed to create DM room"**
   - Verify signalbot commands syntax  
   - Check bridge bot permissions
   - Monitor bridge room for error messages

### Debug Mode

Enable verbose logging:

```python
import logging
logging.getLogger('app.utils.signal_bridge').setLevel(logging.DEBUG)
```

## Legacy Streamlit Integration

If you have existing Streamlit code for Signal bridge operations, you can:

1. **Extract the Matrix client logic** from Streamlit
2. **Adapt the room creation commands** to the new service
3. **Port the message sending logic** to the Flask service
4. **Update event handlers** to call the new webhook

Example migration:

```python
# From Streamlit (legacy)
def send_signal_message_streamlit(uuid, message):
    # Legacy Streamlit Matrix client code
    pass

# To Flask (new)  
async def send_matrix_message(self, room_id, message):
    # New Flask async Matrix client code
    pass
```

## Next Steps

1. **Configure your environment** with Signal bridge settings
2. **Test the resolution handling** using the test script
3. **Set up webhook integration** in your Signal bridge
4. **Monitor the logs** for successful DM creation
5. **Test end-to-end** with actual Signal verification

The key insight is that after `resolve-identifier` succeeds, you need to immediately use the returned UUID with signalbot commands to create the DM and send the verification message. 