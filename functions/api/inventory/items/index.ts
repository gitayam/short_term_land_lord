/**
 * Property Inventory API - List and Create
 * GET  /api/inventory/items - List inventory items
 * POST /api/inventory/items - Create a new inventory item
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

// GET /api/inventory/items
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    // Query parameters
    const propertyId = url.searchParams.get('property_id');
    const category = url.searchParams.get('category');
    const lowStock = url.searchParams.get('low_stock') === 'true';
    const limit = parseInt(url.searchParams.get('limit') || '100');

    // Build query
    let query = `
      SELECT
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
      WHERE 1=1
    `;

    const params: any[] = [];

    // Filter by property ownership (admins see all)
    if (user.role !== 'admin') {
      query += ' AND p.owner_id = ?';
      params.push(user.userId);
    }

    // Apply filters
    if (propertyId) {
      query += ' AND i.property_id = ?';
      params.push(propertyId);
    }

    if (category) {
      query += ' AND i.category = ?';
      params.push(category);
    }

    if (lowStock) {
      query += ' AND i.quantity <= i.min_quantity';
    }

    query += ' ORDER BY i.property_id, i.category, i.name ASC LIMIT ?';
    params.push(limit);

    const items = await env.DB.prepare(query).bind(...params).all();

    // Calculate summary statistics
    let totalItems = 0;
    let lowStockCount = 0;
    let outOfStockCount = 0;

    items.results?.forEach((item: any) => {
      totalItems++;
      if (item.quantity <= item.min_quantity) {
        lowStockCount++;
      }
      if (item.quantity === 0) {
        outOfStockCount++;
      }
    });

    return new Response(
      JSON.stringify({
        success: true,
        items: items.results || [],
        count: items.results?.length || 0,
        summary: {
          total_items: totalItems,
          low_stock_count: lowStockCount,
          out_of_stock_count: outOfStockCount,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Items GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch inventory items',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/inventory/items
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.property_id || !data.name) {
      return new Response(
        JSON.stringify({
          error: 'Property ID and name are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Verify property access
    const property = await env.DB.prepare(
      'SELECT id, owner_id FROM property WHERE id = ?'
    )
      .bind(data.property_id)
      .first();

    if (!property) {
      return new Response(
        JSON.stringify({ error: 'Property not found' }),
        {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    if (user.role !== 'admin' && property.owner_id !== user.userId) {
      return new Response(
        JSON.stringify({ error: 'Access denied to this property' }),
        {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // If catalog_item_id provided, fetch catalog item details
    let unit = data.unit;
    let category = data.category;

    if (data.catalog_item_id) {
      const catalogItem = await env.DB.prepare(
        'SELECT unit, category FROM inventory_catalog_item WHERE id = ?'
      )
        .bind(data.catalog_item_id)
        .first();

      if (!catalogItem) {
        return new Response(
          JSON.stringify({ error: 'Catalog item not found' }),
          {
            status: 404,
            headers: { 'Content-Type': 'application/json' },
          }
        );
      }

      // Use catalog item details if not provided
      unit = unit || catalogItem.unit;
      category = category || catalogItem.category;
    }

    // Validate quantities
    const quantity = parseInt(data.quantity || '0');
    const minQuantity = parseInt(data.min_quantity || '0');

    if (isNaN(quantity) || quantity < 0) {
      return new Response(
        JSON.stringify({ error: 'Quantity must be a non-negative number' }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Create inventory item
    const result = await env.DB.prepare(
      `INSERT INTO inventory_item (
        property_id, catalog_item_id, name, quantity, min_quantity,
        unit, category, location, notes, last_restocked
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.property_id,
        data.catalog_item_id || null,
        data.name,
        quantity,
        minQuantity,
        unit || null,
        category || null,
        data.location || null,
        data.notes || null,
        data.last_restocked || null
      )
      .run();

    // Fetch created item
    const item = await env.DB.prepare(
      `SELECT
        i.id, i.property_id, i.catalog_item_id, i.name,
        i.quantity, i.min_quantity, i.unit, i.category,
        i.location, i.notes, i.last_restocked, i.created_at,
        p.name as property_name
      FROM inventory_item i
      LEFT JOIN property p ON i.property_id = p.id
      WHERE i.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        item,
        message: 'Inventory item created successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Items POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create inventory item',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
