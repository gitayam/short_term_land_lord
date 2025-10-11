/**
 * Inventory Quantity Adjustment API
 * POST /api/inventory/items/[id]/adjust - Adjust inventory quantity (add/subtract)
 */

import { Env } from '../../../../_middleware';
import { requireAuth } from '../../../../utils/auth';

// POST /api/inventory/items/[id]/adjust
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env, params } = context;

  try {
    const user = await requireAuth(request, env);
    const itemId = params.id as string;
    const data = await request.json();

    // Validate adjustment
    if (data.adjustment === undefined) {
      return new Response(
        JSON.stringify({
          error: 'Adjustment value is required',
          example: { adjustment: 10 } // positive to add, negative to subtract
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    const adjustment = parseInt(data.adjustment);
    if (isNaN(adjustment)) {
      return new Response(
        JSON.stringify({ error: 'Adjustment must be a number' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

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

    // Calculate new quantity
    const currentQuantity = item.quantity as number;
    const newQuantity = currentQuantity + adjustment;

    // Prevent negative quantities
    if (newQuantity < 0) {
      return new Response(
        JSON.stringify({
          error: 'Adjustment would result in negative quantity',
          current_quantity: currentQuantity,
          requested_adjustment: adjustment,
          would_result_in: newQuantity,
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Update quantity (and last_restocked if adding stock)
    const updates = ['quantity = ?', 'updated_at = datetime("now")'];
    const params: any[] = [newQuantity];

    if (adjustment > 0) {
      updates.push('last_restocked = date("now")');
    }

    params.push(itemId);

    await env.DB.prepare(
      `UPDATE inventory_item SET ${updates.join(', ')} WHERE id = ?`
    )
      .bind(...params)
      .run();

    // Fetch updated item
    const updatedItem = await env.DB.prepare(
      `SELECT
        i.id, i.property_id, i.name, i.quantity, i.min_quantity,
        i.unit, i.category, i.location, i.last_restocked,
        p.name as property_name
      FROM inventory_item i
      LEFT JOIN property p ON i.property_id = p.id
      WHERE i.id = ?`
    )
      .bind(itemId)
      .first();

    // Check if now low stock
    const isLowStock = updatedItem && (updatedItem.quantity as number) <= (updatedItem.min_quantity as number);

    return new Response(
      JSON.stringify({
        success: true,
        item: updatedItem,
        adjustment: {
          previous_quantity: currentQuantity,
          adjustment_amount: adjustment,
          new_quantity: newQuantity,
          is_low_stock: isLowStock,
        },
        message: adjustment > 0 ? 'Stock added successfully' : 'Stock consumed successfully',
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Adjust] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to adjust inventory',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
