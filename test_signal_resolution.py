#!/usr/bin/env python3
"""
Test script to manually trigger Signal identifier resolution handling
This simulates what should happen after the Signal bridge resolves +12247253276 to 770b19f5-389e-444e-8976-551a52136cf6
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_signal_resolution():
    """Test the Signal identifier resolution handling"""
    try:
        from app import create_app
        from app.utils.signal_bridge import handle_signal_resolution
        
        # Create app context
        app = create_app()
        
        with app.app_context():
            print("🔍 Testing Signal identifier resolution handling...")
            print("=" * 60)
            
            # Use the actual values from the user's example
            phone_number = "+12247253276"
            signal_uuid = "770b19f5-389e-444e-8976-551a52136cf6"
            display_name = "Sac"  # From the user's description
            
            print(f"📱 Phone Number: {phone_number}")
            print(f"🆔 Signal UUID: {signal_uuid}")
            print(f"👤 Display Name: {display_name}")
            print()
            
            # Handle the resolution
            print("🚀 Handling identifier resolution...")
            await handle_signal_resolution(phone_number, signal_uuid, display_name)
            
            print("✅ Resolution handling completed!")
            print()
            print("Expected flow:")
            print("1. ✅ Find user in database by phone number")
            print("2. ✅ Check for existing DM room with Signal UUID")
            print("3. ✅ Create new private message room if needed")
            print("4. ✅ Send preparatory message: '🔐 Securing message...'")
            print("5. ✅ Wait for encryption establishment")
            print("6. ✅ Send verification message")
            print("7. ✅ Store Signal interaction in database")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_webhook_payload():
    """Test the webhook payload handling"""
    try:
        from app import create_app
        import json
        
        app = create_app()
        
        with app.test_client() as client:
            print("\n🌐 Testing Signal webhook endpoint...")
            print("=" * 60)
            
            # Simulate the webhook payload that would be sent after identifier resolution
            webhook_payload = {
                "type": "identifier_resolved",
                "phone_number": "+12247253276",
                "signal_uuid": "770b19f5-389e-444e-8976-551a52136cf6",
                "display_name": "Sac",
                "timestamp": "2025-01-16T19:30:00Z",
                "bridge_room_id": "!example:matrix.org"
            }
            
            print(f"📤 Sending webhook payload:")
            print(json.dumps(webhook_payload, indent=2))
            print()
            
            # Send POST request to webhook endpoint
            response = client.post(
                '/messages/signal-webhook',
                json=webhook_payload,
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📥 Response Status: {response.status_code}")
            print(f"📥 Response Data: {response.get_json()}")
            
            if response.status_code == 200:
                print("✅ Webhook endpoint processed the payload successfully!")
            else:
                print("❌ Webhook endpoint returned an error")
                
    except Exception as e:
        print(f"❌ Error during webhook test: {str(e)}")
        import traceback
        traceback.print_exc()

def print_configuration():
    """Print current Signal bridge configuration"""
    print("⚙️  Current Signal Bridge Configuration:")
    print("=" * 60)
    
    config_vars = [
        'SIGNAL_BRIDGE_ENABLED',
        'SIGNAL_BRIDGE_ROOM_ID', 
        'MATRIX_BOT_USER_ID',
        'MATRIX_API_BASE',
        'MATRIX_ACCESS_TOKEN',
        'MATRIX_HOMESERVER',
        'SIGNAL_WEBHOOK_URL'
    ]
    
    for var in config_vars:
        value = os.environ.get(var, 'Not set')
        # Mask sensitive values
        if 'TOKEN' in var and value != 'Not set':
            value = value[:8] + "..." if len(value) > 8 else "***"
        print(f"{var}: {value}")
    
    print()

def print_usage():
    """Print usage instructions"""
    print("📚 Usage Instructions:")
    print("=" * 60)
    print("1. Configure your .env file with Signal bridge settings:")
    print("   SIGNAL_BRIDGE_ENABLED=true")
    print("   SIGNAL_BRIDGE_ROOM_ID=!your_bridge_room:matrix.org")
    print("   MATRIX_BOT_USER_ID=@your_bot:matrix.org")
    print("   MATRIX_ACCESS_TOKEN=your_matrix_token")
    print()
    print("2. Run this script to test the resolution handling:")
    print("   python test_signal_resolution.py")
    print()
    print("3. In your Signal bridge room, you can manually trigger:")
    print("   resolve-identifier +12247253276")
    print()
    print("4. After resolution, call the webhook endpoint:")
    print("   POST /messages/signal-webhook")
    print("   with the resolution data")
    print()

async def main():
    """Main test function"""
    print("🔧 Signal Bridge Resolution Test")
    print("=" * 60)
    print()
    
    print_configuration()
    print_usage()
    
    # Check if Signal bridge is enabled
    if os.environ.get('SIGNAL_BRIDGE_ENABLED', 'false').lower() != 'true':
        print("⚠️  Signal bridge is not enabled in configuration")
        print("   Set SIGNAL_BRIDGE_ENABLED=true in your .env file")
        return
    
    # Run tests
    await test_signal_resolution()
    await test_webhook_payload()
    
    print("\n🎯 Next Steps:")
    print("1. Check the logs for any errors")
    print("2. Verify your Matrix client can see the bot's activity")
    print("3. Test with your actual Signal bridge setup")
    print("4. Monitor the Signal bridge room for successful DM creation")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 