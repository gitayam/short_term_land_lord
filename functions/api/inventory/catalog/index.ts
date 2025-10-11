/**
 * Inventory Catalog API - List and Create
 * GET  /api/inventory/catalog - List catalog items
 * POST /api/inventory/catalog - Create a new catalog item
 */

import { Env } from '../../../_middleware';
import { requireAuth } from '../../../utils/auth';

// Inventory categories
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

// GET /api/inventory/catalog
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    // Query parameters
    const category = url.searchParams.get('category');
    const search = url.searchParams.get('search');
    const limit = parseInt(url.searchParams.get('limit') || '100');

    // Build query
    let query = `
      SELECT
        ic.id, ic.name, ic.description, ic.category,
        ic.unit, ic.unit_price, ic.sku, ic.barcode,
        ic.purchase_link, ic.currency,
        ic.created_at, ic.updated_at,
        u.first_name as creator_first_name,
        u.last_name as creator_last_name
      FROM inventory_catalog_item ic
      LEFT JOIN users u ON ic.creator_id = u.id
      WHERE 1=1
    `;

    const params: any[] = [];

    // Apply filters
    if (category) {
      query += ' AND ic.category = ?';
      params.push(category);
    }

    if (search) {
      query += ' AND (ic.name LIKE ? OR ic.description LIKE ? OR ic.sku LIKE ?)';
      const searchPattern = `%${search}%`;
      params.push(searchPattern, searchPattern, searchPattern);
    }

    query += ' ORDER BY ic.category, ic.name ASC LIMIT ?';
    params.push(limit);

    const items = await env.DB.prepare(query).bind(...params).all();

    return new Response(
      JSON.stringify({
        success: true,
        items: items.results || [],
        count: items.results?.length || 0,
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Catalog GET] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to fetch catalog items',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};

// POST /api/inventory/catalog
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const data = await request.json();

    // Validate required fields
    if (!data.name || !data.unit || !data.unit_price) {
      return new Response(
        JSON.stringify({
          error: 'Name, unit, and unit price are required',
        }),
        {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
        }
      );
    }

    // Validate category
    const category = data.category || 'general';
    if (!INVENTORY_CATEGORIES.includes(category)) {
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

    // Validate unit price
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

    // Create catalog item
    const result = await env.DB.prepare(
      `INSERT INTO inventory_catalog_item (
        name, description, category, unit, unit_price,
        sku, barcode, purchase_link, currency, creator_id
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        data.name,
        data.description || null,
        category,
        data.unit,
        unitPrice,
        data.sku || null,
        data.barcode || null,
        data.purchase_link || null,
        data.currency || 'USD',
        user.userId
      )
      .run();

    // Fetch created item
    const item = await env.DB.prepare(
      `SELECT
        ic.id, ic.name, ic.description, ic.category,
        ic.unit, ic.unit_price, ic.sku, ic.barcode,
        ic.purchase_link, ic.currency, ic.created_at
      FROM inventory_catalog_item ic
      WHERE ic.id = ?`
    )
      .bind(result.meta.last_row_id)
      .first();

    return new Response(
      JSON.stringify({
        success: true,
        item,
        message: 'Catalog item created successfully',
      }),
      {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Inventory Catalog POST] Error:', error);
    return new Response(
      JSON.stringify({
        error: 'Failed to create catalog item',
        message: error.message,
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
