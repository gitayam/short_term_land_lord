/**
 * Property Room Management API
 * PUT /api/properties/[id]/rooms/[roomId] - Update room
 * DELETE /api/properties/[id]/rooms/[roomId] - Delete room
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

interface PropertyRoom {
  id: string;
  property_id: string;
  room_type: 'bedroom' | 'bathroom' | 'kitchen' | 'living_room' | 'other';
  name: string | null;
  bed_type: string | null;
  bed_count: number;
  has_ensuite: number;
  amenities: string | null;
  notes: string | null;
  display_order: number;
}

// PUT /api/properties/[id]/rooms/[roomId]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const roomId = params.roomId as string;

    // Verify property ownership
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if ((property as any).owner_id !== user.userId && user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify room exists and belongs to property
    const room = await env.DB.prepare(
      'SELECT * FROM property_room WHERE id = ? AND property_id = ?'
    )
      .bind(roomId, propertyId)
      .first();

    if (!room) {
      return new Response(
        JSON.stringify({ error: 'Room not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const data = await request.json();

    // Validate room_type if provided
    if (data.room_type) {
      const validRoomTypes = ['bedroom', 'bathroom', 'kitchen', 'living_room', 'other'];
      if (!validRoomTypes.includes(data.room_type)) {
        return new Response(
          JSON.stringify({
            error: `room_type must be one of: ${validRoomTypes.join(', ')}`,
          }),
          { status: 400, headers: { 'Content-Type': 'application/json' } }
        );
      }
    }

    // Update room with COALESCE pattern (only update provided fields)
    await env.DB.prepare(
      `UPDATE property_room SET
        room_type = COALESCE(?, room_type),
        name = COALESCE(?, name),
        bed_type = COALESCE(?, bed_type),
        bed_count = COALESCE(?, bed_count),
        has_ensuite = COALESCE(?, has_ensuite),
        amenities = COALESCE(?, amenities),
        notes = COALESCE(?, notes),
        display_order = COALESCE(?, display_order)
      WHERE id = ?`
    )
      .bind(
        data.room_type !== undefined ? data.room_type : null,
        data.name !== undefined ? data.name : null,
        data.bed_type !== undefined ? data.bed_type : null,
        data.bed_count !== undefined ? data.bed_count : null,
        data.has_ensuite !== undefined ? data.has_ensuite : null,
        data.amenities !== undefined ? data.amenities : null,
        data.notes !== undefined ? data.notes : null,
        data.display_order !== undefined ? data.display_order : null,
        roomId
      )
      .run();

    // Get updated room
    const updated = await env.DB.prepare(
      'SELECT * FROM property_room WHERE id = ?'
    )
      .bind(roomId)
      .first<PropertyRoom>();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Room updated successfully',
        room: updated,
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Room PUT] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to update room' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/properties/[id]/rooms/[roomId]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;
    const roomId = params.roomId as string;

    // Verify property ownership
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(propertyId)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    if ((property as any).owner_id !== user.userId && user.role !== 'admin') {
      return new Response(
        JSON.stringify({ error: 'Unauthorized' }),
        { status: 403, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Verify room exists and belongs to property
    const room = await env.DB.prepare(
      'SELECT * FROM property_room WHERE id = ? AND property_id = ?'
    )
      .bind(roomId, propertyId)
      .first();

    if (!room) {
      return new Response(
        JSON.stringify({ error: 'Room not found' }),
        { status: 404, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Delete room
    await env.DB.prepare('DELETE FROM property_room WHERE id = ?')
      .bind(roomId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Room deleted successfully',
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Room DELETE] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to delete room' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
