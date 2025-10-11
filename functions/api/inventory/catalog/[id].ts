/**
 * Inventory Catalog API - Get, Update, Delete by ID
 * GET    /api/inventory/catalog/[id] - Get catalog item details
 * PUT    /api/inventory/catalog/[id] - Update catalog item
 * DELETE /api/inventory/catalog/[id] - Delete catalog item
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

const INVENTORY_CATEGORIES = [
  'linens',
  'toiletries',
  'cleaning_supplies',
  'kitchen',
  'appliances',
  'furniture',
  'electronics',
  'amenities',
  'maintenance',
  'safety',
  'general',
];

// GET /api/inventory/catalog/[id]
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;

    const item = await env.DB.prepare(
      `SELECT
        ic.id, ic.name, ic.description, ic.category,
        ic.unit, ic.unit_price, ic.sku, ic.barcode,
        ic.purchase_link, ic.currency,
        ic.created_at, ic.updated_at,
        u.first_name as creator_first_name,
        u.last_name as creator_last_name
      FROM inventory_catalog_item ic
      LEFT JOIN users u ON ic.creator_id = u.id
      WHERE ic.id = ?`
    )
      .bind(itemId)
      .first();

    if (!item) {
      return new Response(
        JSON.stringify({ error: 'Catalog item not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Count usage in properties
    const usage = await env.DB.prepare(
      `SELECT COUNT(*) as count
       FROM inventory_item
       WHERE catalog_item_id = ?`
    )
      .bind(itemId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        item: {
          ...item,
          usage_count: usage?.count || 0,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Catalog GET by ID] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch catalog item',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// PUT /api/inventory/catalog/[id]
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;
    const data = await request.json();

    // Fetch existing item
    const item = await env.DB.prepare(
      'SELECT * FROM inventory_catalog_item WHERE id = ?'
    )
      .bind(itemId)
      .first();

    if (!item) {
      return new Response(
        JSON.stringify({ error: 'Catalog item not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Build update query dynamically
    const updates: string[] = [];
    const params: any[] = [];

    if (data.name !== undefined) {
      updates.push('name = ?');
      params.push(data.name);
    }
    if (data.description !== undefined) {
      updates.push('description = ?');
      params.push(data.description);
    }
    if (data.category !== undefined) {
      if (!INVENTORY_CATEGORIES.includes(data.category)) {
        return new Response(
          JSON.stringify({
            error: 'Invalid category',
            valid_categories: INVENTORY_CATEGORIES,
          }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
      updates.push('category = ?');
      params.push(data.category);
    }
    if (data.unit !== undefined) {
      updates.push('unit = ?');
      params.push(data.unit);
    }
    if (data.unit_price !== undefined) {
      const unitPrice = parseFloat(data.unit_price);
      if (isNaN(unitPrice) || unitPrice < 0) {
        return new Response(
          JSON.stringify({ error: 'Unit price must be a non-negative number' }),
          {
            status: 400,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }
      updates.push('unit_price = ?');
      params.push(unitPrice);
    }
    if (data.sku !== undefined) {
      updates.push('sku = ?');
      params.push(data.sku);
    }
    if (data.barcode !== undefined) {
      updates.push('barcode = ?');
      params.push(data.barcode);
    }
    if (data.purchase_link !== undefined) {
      updates.push('purchase_link = ?');
      params.push(data.purchase_link);
    }
    if (data.currency !== undefined) {
      updates.push('currency = ?');
      params.push(data.currency);
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
      `UPDATE inventory_catalog_item SET ${updates.join(', ')} WHERE id = ?`
    )
      .bind(...params)
      .run();

    // Fetch updated item
    const updatedItem = await env.DB.prepare(
      `SELECT
        ic.id, ic.name, ic.description, ic.category,
        ic.unit, ic.unit_price, ic.sku, ic.barcode,
        ic.purchase_link, ic.currency,
        ic.created_at, ic.updated_at
      FROM inventory_catalog_item ic
      WHERE ic.id = ?`
    )
      .bind(itemId)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        item: updatedItem,
        message: 'Catalog item updated successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Catalog PUT] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to update catalog item',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// DELETE /api/inventory/catalog/[id]
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;

    // Fetch item
    const item = await env.DB.prepare(
      'SELECT * FROM inventory_catalog_item WHERE id = ?'
    )
      .bind(itemId)
      .first();

    if (!item) {
      return new Response(
        JSON.stringify({ error: 'Catalog item not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Check if item is in use
    const usage = await env.DB.prepare(
      `SELECT COUNT(*) as count
       FROM inventory_item
       WHERE catalog_item_id = ?`
    )
      .bind(itemId)
      .first();

    if (usage && (usage.count as number) > 0) {
      return new Response(
        JSON.stringify({
          error: 'Cannot delete catalog item that is in use',
          usage_count: usage.count,
          suggestion: 'Remove this item from all properties first',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Delete item
    await env.DB.prepare('DELETE FROM inventory_catalog_item WHERE id = ?')
      .bind(itemId)
      .run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Catalog item deleted successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Catalog DELETE] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to delete catalog item',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
