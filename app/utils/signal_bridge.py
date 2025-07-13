"""
Signal Bridge Integration for Direct Messaging
Handles post-identifier resolution steps for Signal verification
"""
import asyncio
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from flask import current_app
from app.models import User, MessageThread, Message, db
from app.utils.sms import format_phone_number

logger = logging.getLogger(__name__)

class SignalBridgeService:
    """Service for handling Signal bridge operations and direct messaging"""
    
    def __init__(self):
        self.bridge_room_id = current_app.config.get('SIGNAL_BRIDGE_ROOM_ID')
        self.bot_user_id = current_app.config.get('MATRIX_BOT_USER_ID')
        self.matrix_api_base = current_app.config.get('MATRIX_API_BASE', 'https://matrix.org')
        
    async def handle_identifier_resolved(self, phone_number: str, signal_uuid: str, user_data: Dict[str, Any]) -> bool:
        """
        Handle the next steps after Signal identifier resolution
        
        Args:
            phone_number: The resolved phone number (e.g., +12247253276)
            signal_uuid: The resolved Signal UUID (e.g., 770b19f5-389e-444e-8976-551a52136cf6)
            user_data: Additional user data from the resolution
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            logger.info(f"Processing resolved identifier: {phone_number} -> {signal_uuid}")
            
            # Find the user in our database
            formatted_phone = format_phone_number(phone_number)
            user = User.query.filter_by(phone=formatted_phone).first()
            
            if not user:
                logger.warning(f"No user found for phone number {formatted_phone}")
                return False
            
            # Check for existing DM room
            existing_room_id = await self.find_existing_dm_room(signal_uuid)
            
            if existing_room_id:
                logger.info(f"Found existing DM room: {existing_room_id}")
                room_id = existing_room_id
            else:
                # Create new private message room
                room_id = await self.create_private_message_room(signal_uuid, user.get_full_name())
                if not room_id:
                    logger.error("Failed to create private message room")
                    return False
                logger.info(f"Created new DM room: {room_id}")
            
            # Send verification message
            success = await self.send_verification_message(room_id, user, signal_uuid)
            
            if success:
                # Store the interaction in our database
                self.store_signal_interaction(user.id, phone_number, signal_uuid, room_id)
                
            return success
            
        except Exception as e:
            logger.error(f"Error handling identifier resolution: {str(e)}", exc_info=True)
            return False
    
    async def find_existing_dm_room(self, signal_uuid: str) -> Optional[str]:
        """
        Find existing DM room with the Signal user
        
        Args:
            signal_uuid: The Signal UUID to look for
            
        Returns:
            Optional[str]: Room ID if found, None otherwise
        """
        try:
            # Use Matrix API to search for existing rooms
            # This would typically involve querying the Matrix client for rooms
            # where the bot and the Signal user are both members
            
            # For now, we'll use a placeholder implementation
            # In a real implementation, you'd query the Matrix client:
            # rooms = await matrix_client.get_rooms()
            # for room in rooms:
            #     members = await matrix_client.get_room_members(room.room_id)
            #     if signal_uuid in [member.user_id for member in members]:
            #         return room.room_id
            
            logger.info(f"Searching for existing DM room with {signal_uuid}")
            return None  # Placeholder - implement actual room search
            
        except Exception as e:
            logger.error(f"Error finding existing DM room: {str(e)}")
            return None
    
    async def create_private_message_room(self, signal_uuid: str, display_name: str) -> Optional[str]:
        """
        Create a new private message room
        
        Args:
            signal_uuid: The Signal UUID to invite
            display_name: Display name for the room
            
        Returns:
            Optional[str]: Room ID if created successfully
        """
        try:
            logger.info(f"Creating private message room for {signal_uuid}")
            
            # Use signalbot command to create DM
            # This mirrors the legacy Streamlit implementation pattern
            signalbot_command = f"!signal pm {signal_uuid}"
            
            # Send command to Signal bridge room
            command_sent = await self.send_bridge_command(signalbot_command)
            
            if command_sent:
                # Wait a moment for room creation
                await asyncio.sleep(2)
                
                # Get the newly created room ID
                # This would typically involve monitoring for new room invitations
                # or checking recent room creation events
                new_room_id = await self.get_latest_dm_room(signal_uuid)
                return new_room_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating private message room: {str(e)}")
            return None
    
    async def send_verification_message(self, room_id: str, user: User, signal_uuid: str) -> bool:
        """
        Send verification message to the Signal user
        Includes preparatory message for encryption setup
        
        Args:
            room_id: Matrix room ID
            user: User object from database
            signal_uuid: Signal UUID
            
        Returns:
            bool: True if sent successfully
        """
        try:
            logger.info(f"Sending verification message to room {room_id}")
            
            # Send preparatory message first to establish encryption
            prep_message = "🔐 Securing message..."
            prep_sent = await self.send_matrix_message(room_id, prep_message)
            
            if prep_sent:
                # Wait for Element to establish encryption
                await asyncio.sleep(3)
                
                # Send the actual verification message
                verification_message = self.generate_verification_message(user)
                return await self.send_matrix_message(room_id, verification_message)
            
            return False
            
        except Exception as e:
            logger.error(f"Error sending verification message: {str(e)}")
            return False
    
    def generate_verification_message(self, user: User) -> str:
        """
        Generate the verification message content
        
        Args:
            user: User object
            
        Returns:
            str: Verification message
        """
        message = f"""✅ Signal Verification for {user.get_full_name()}

Your phone number has been successfully verified for the Short Term Landlord Property Management System.

📱 Phone: {user.phone}
📧 Email: {user.email}
🏢 Role: {user.role}

You can now:
• Receive SMS notifications for tasks and updates
• Reply to this message for direct communication
• Use 'HELP' for available commands

Welcome to the system! 🎉"""
        
        return message
    
    async def send_bridge_command(self, command: str) -> bool:
        """
        Send command to Signal bridge room
        
        Args:
            command: Signalbot command to send
            
        Returns:
            bool: True if sent successfully
        """
        try:
            if not self.bridge_room_id:
                logger.error("Signal bridge room ID not configured")
                return False
            
            return await self.send_matrix_message(self.bridge_room_id, command)
            
        except Exception as e:
            logger.error(f"Error sending bridge command: {str(e)}")
            return False
    
    async def send_matrix_message(self, room_id: str, message: str) -> bool:
        """
        Send message to Matrix room
        
        Args:
            room_id: Target room ID
            message: Message content
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # This would use your Matrix client implementation
            # For now, this is a placeholder that logs the action
            logger.info(f"Sending Matrix message to {room_id}: {message[:50]}...")
            
            # In a real implementation, you'd use something like:
            # await matrix_client.room_send(
            #     room_id=room_id,
            #     message_type="m.room.message",
            #     content={
            #         "msgtype": "m.text",
            #         "body": message
            #     }
            # )
            
            # For testing, we'll simulate success
            return True
            
        except Exception as e:
            logger.error(f"Error sending Matrix message: {str(e)}")
            return False
    
    async def get_latest_dm_room(self, signal_uuid: str) -> Optional[str]:
        """
        Get the most recently created DM room with the specified Signal user
        
        Args:
            signal_uuid: Signal UUID to find room for
            
        Returns:
            Optional[str]: Room ID if found
        """
        try:
            # This would involve checking recent room invitations or events
            # Placeholder implementation
            logger.info(f"Looking for latest DM room with {signal_uuid}")
            return None  # Implement actual room detection
            
        except Exception as e:
            logger.error(f"Error getting latest DM room: {str(e)}")
            return None
    
    def store_signal_interaction(self, user_id: int, phone_number: str, signal_uuid: str, room_id: str):
        """
        Store Signal interaction in database for tracking
        
        Args:
            user_id: User ID
            phone_number: Phone number
            signal_uuid: Signal UUID
            room_id: Matrix room ID
        """
        try:
            # Update user record with Signal info
            user = User.query.get(user_id)
            if user:
                user.signal_identity = signal_uuid
                
                # Create a message thread for tracking
                thread = MessageThread(
                    participant_phone=phone_number,
                    system_phone="signal_bridge",
                    status='active',
                    user_id=user_id
                )
                db.session.add(thread)
                
                # Create initial message record
                message = Message(
                    thread_id=thread.id,
                    direction='outgoing',
                    phone_number=phone_number,
                    content=f"Signal verification sent to room {room_id}",
                    external_id=signal_uuid,
                    status='sent'
                )
                db.session.add(message)
                
                db.session.commit()
                logger.info(f"Stored Signal interaction for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error storing Signal interaction: {str(e)}")
            db.session.rollback()

class SignalVerificationHandler:
    """Handler for phone number verification via Signal bridge"""
    
    def __init__(self):
        self.bridge_service = SignalBridgeService()
    
    async def verify_phone_number(self, phone_number: str) -> Tuple[bool, str]:
        """
        Initiate phone number verification via Signal
        
        Args:
            phone_number: Phone number to verify
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            logger.info(f"Starting Signal verification for {phone_number}")
            
            # Step 1: Send resolve-identifier command
            resolve_command = f"resolve-identifier {phone_number}"
            command_sent = await self.bridge_service.send_bridge_command(resolve_command)
            
            if not command_sent:
                return False, "Failed to send resolve command to Signal bridge"
            
            # Step 2: Wait for resolution (this would typically be handled by event listeners)
            # For now, we'll simulate the resolution result
            # In practice, you'd have event handlers that call handle_identifier_resolved
            
            logger.info(f"Resolve command sent for {phone_number}")
            return True, f"Signal verification initiated for {phone_number}"
            
        except Exception as e:
            logger.error(f"Error in phone verification: {str(e)}")
            return False, f"Verification failed: {str(e)}"
    
    async def handle_resolution_result(self, phone_number: str, signal_uuid: str, display_name: str = "Unknown"):
        """
        Handle the result of identifier resolution
        This would typically be called by a webhook or event listener
        
        Args:
            phone_number: Resolved phone number
            signal_uuid: Resolved Signal UUID
            display_name: Display name from Signal
        """
        try:
            user_data = {
                'display_name': display_name,
                'resolved_at': datetime.utcnow()
            }
            
            success = await self.bridge_service.handle_identifier_resolved(
                phone_number, signal_uuid, user_data
            )
            
            if success:
                logger.info(f"Successfully handled resolution for {phone_number}")
            else:
                logger.error(f"Failed to handle resolution for {phone_number}")
                
        except Exception as e:
            logger.error(f"Error handling resolution result: {str(e)}")

# Convenience functions for Flask routes
signal_bridge = SignalBridgeService()
verification_handler = SignalVerificationHandler()

async def verify_user_phone(phone_number: str) -> Tuple[bool, str]:
    """Verify a user's phone number via Signal bridge"""
    return await verification_handler.verify_phone_number(phone_number)

async def handle_signal_resolution(phone_number: str, signal_uuid: str, display_name: str = "User"):
    """Handle Signal identifier resolution result"""
    await verification_handler.handle_resolution_result(phone_number, signal_uuid, display_name) 