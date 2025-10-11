/**
 * Property Inventory API - Get, Update, Delete by ID
 * GET    /api/inventory/items/[id] - Get inventory item details
 * PUT    /api/inventory/items/[id] - Update inventory item
 * DELETE /api/inventory/items/[id] - Delete inventory item
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

// GET /api/inventory/items/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;

    const item = await env.DB.prepare(
      `SELECT
        i.id, i.property_id, i.catalog_item_id, i.name,
        i.quantity, i.min_quantity, i.unit, i.category,
        i.location, i.notes, i.last_restocked,
        i.created_at, i.updated_at,
        p.name as property_name,
        p.address as property_address,
        ic.unit_price, ic.sku, ic.barcode, ic.purchase_link
      FROM inventory_item i
      LEFT JOIN property p ON i.property_id = p.id
      LEFT JOIN inventory_catalog_item ic ON i.catalog_item_id = ic.id
      WHERE i.id = ?`
    )
      .bind(itemId)
      .first();

    if (!item) {
      return new Response(
        JSON.stringify({ error: 'Inventory item not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      const property = await env.DB.prepare(
        'SELECT owner_id FROM property WHERE id = ?'
      )
        .bind(item.property_id)
        .first();

      if (property && property.owner_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        item,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Items GET by ID] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch inventory item',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/inventory/items/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;
    const data = await request.json();

    // Fetch existing item
    const item = await env.DB.prepare(
      'SELECT * FROM inventory_item WHERE id = ?'
    )
      .bind(itemId)
      .first();

    if (!item) {
      return new Response(
        JSON.stringify({ error: 'Inventory item not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      const property = await env.DB.prepare(
        'SELECT owner_id FROM property WHERE id = ?'
      )
        .bind(item.property_id)
        .first();

      if (property && property.owner_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Build update query dynamically
    const updates: string[] = [];
    const params: any[] = [];

    if (data.name !== undefined) {
      updates.push('name = ?');
      params.push(data.name);
    }
    if (data.quantity !== undefined) {
      const quantity = parseInt(data.quantity);
      if (isNaN(quantity) || quantity < 0) {
        return new Response(
          JSON.stringify({ error: 'Quantity must be a non-negative number' }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
      updates.push('quantity = ?');
      params.push(quantity);
    }
    if (data.min_quantity !== undefined) {
      const minQuantity = parseInt(data.min_quantity);
      if (isNaN(minQuantity) || minQuantity < 0) {
        return new Response(
          JSON.stringify({ error: 'Min quantity must be a non-negative number' }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
      updates.push('min_quantity = ?');
      params.push(minQuantity);
    }
    if (data.unit !== undefined) {
      updates.push('unit = ?');
      params.push(data.unit);
    }
    if (data.category !== undefined) {
      updates.push('category = ?');
      params.push(data.category);
    }
    if (data.location !== undefined) {
      updates.push('location = ?');
      params.push(data.location);
    }
    if (data.notes !== undefined) {
      updates.push('notes = ?');
      params.push(data.notes);
    }
    if (data.last_restocked !== undefined) {
      updates.push('last_restocked = ?');
      params.push(data.last_restocked);
    }

    if (updates.length === 0) {
      return new Response(
        JSON.stringify({ error: 'No fields to update' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Always update updated_at
    updates.push('updated_at = datetime("now")');
    params.push(itemId);

    // Execute update
    await env.DB.prepare(
      `UPDATE inventory_item SET ${updates.join(', ')} WHERE id = ?`
    )
      .bind(...params)
      .run();

    // Fetch updated item
    const updatedItem = await env.DB.prepare(
      `SELECT
        i.id, i.property_id, i.name, i.quantity, i.min_quantity,
        i.unit, i.category, i.location, i.notes, i.last_restocked,
        i.created_at, i.updated_at,
        p.name as property_name
      FROM inventory_item i
      LEFT JOIN property p ON i.property_id = p.id
      WHERE i.id = ?`
    )
      .bind(itemId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        item: updatedItem,
        message: 'Inventory item updated successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Items PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to update inventory item',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/inventory/items/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;

    // Fetch item
    const item = await env.DB.prepare(
      'SELECT * FROM inventory_item WHERE id = ?'
    )
      .bind(itemId)
      .first();

    if (!item) {
      return new Response(
        JSON.stringify({ error: 'Inventory item not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check access rights
    if (user.role !== 'admin') {
      const property = await env.DB.prepare(
        'SELECT owner_id FROM property WHERE id = ?'
      )
        .bind(item.property_id)
        .first();

      if (property && property.owner_id !== user.userId) {
        return new Response(
          JSON.stringify({ error: 'Access denied' }),
          {
            status: 403,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
    }

    // Delete item
    await env.DB.prepare('DELETE FROM inventory_item WHERE id = ?')
      .bind(itemId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Inventory item deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Items DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete inventory item',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
