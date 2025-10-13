/**
 * Property Rooms API
 * GET /api/properties/[id]/rooms - List all rooms
 * POST /api/properties/[id]/rooms - Create new room
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

// GET /api/properties/[id]/rooms
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

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

    // Get all rooms ordered by display_order
    const rooms = await env.DB.prepare(
      'SELECT * FROM property_room WHERE property_id = ? ORDER BY display_order ASC, room_type ASC'
    )
      .bind(propertyId)
      .all<PropertyRoom>();

    return new Response(
      JSON.stringify({
        success: true,
        rooms: rooms.results || [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Rooms GET] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to fetch rooms' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/properties/[id]/rooms
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { params, request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const propertyId = params.id as string;

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

    const data = await request.json();
    const {
      room_type,
      name,
      bed_type,
      bed_count = 0,
      has_ensuite = 0,
      amenities,
      notes,
    } = data;

    // Validate room_type
    const validRoomTypes = ['bedroom', 'bathroom', 'kitchen', 'living_room', 'other'];
    if (!room_type || !validRoomTypes.includes(room_type)) {
      return new Response(
        JSON.stringify({
          error: `room_type is required and must be one of: ${validRoomTypes.join(', ')}`,
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Get current max display_order
    const maxOrder = await env.DB.prepare(
      'SELECT MAX(display_order) as max_order FROM property_room WHERE property_id = ?'
    )
      .bind(propertyId)
      .first();

    const displayOrder = ((maxOrder as any)?.max_order || 0) + 1;

    // Insert room record
    await env.DB.prepare(
      `INSERT INTO property_room (property_id, room_type, name, bed_type, bed_count, has_ensuite, amenities, notes, display_order)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        propertyId,
        room_type,
        name || null,
        bed_type || null,
        bed_count,
        has_ensuite,
        amenities || null,
        notes || null,
        displayOrder
      )
      .run();

    // Get the created room
    const created = await env.DB.prepare(
      'SELECT * FROM property_room WHERE property_id = ? ORDER BY display_order DESC LIMIT 1'
    )
      .bind(propertyId)
      .first<PropertyRoom>();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Room created successfully',
        room: created,
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('[Property Rooms POST] Error:', error);
    return new Response(
      JSON.stringify({ error: error.message || 'Failed to create room' }),
      {
        status: error.message === 'Unauthorized' || error.message === 'Session expired' ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
