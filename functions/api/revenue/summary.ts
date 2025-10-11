/**
 * Revenue Summary API
 * GET /api/revenue/summary - Get revenue summary by period and property
 */

import { Env } from '../../_middleware';
import { requireAuth } from '../../utils/auth';

// GET /api/revenue/summary
export const onRequestGet: PagesFunction<Env> = async (context) => {
  const { request, env } = context;

  try {
    const user = await requireAuth(request, env);
    const url = new URL(request.url);

    const propertyId = url.searchParams.get('property_id');
    const startDate = url.searchParams.get('start_date');
    const endDate = url.searchParams.get('end_date');
    const groupBy = url.searchParams.get('group_by') || 'month'; // month, quarter, year

    // Build base query
    let query = `
      SELECT
        r.property_id,
        p.name as property_name,
        r.source,
        r.status,
        SUM(r.amount) as total_amount,
        COUNT(*) as count
      FROM revenue r
      LEFT JOIN property p ON r.property_id = p.id
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
      query += ' AND r.property_id = ?';
      params.push(propertyId);
    }

    if (startDate) {
      query += ' AND r.revenue_date >= ?';
      params.push(startDate);
    }

    if (endDate) {
      query += ' AND r.revenue_date <= ?';
      params.push(endDate);
    }

    // Group by property and source
    query += ' GROUP BY r.property_id, r.source, r.status ORDER BY property_name, r.source';

    const results = await env.DB.prepare(query).bind(...params).all();

    // Calculate totals
    let totalRevenue = 0;
    let totalReceived = 0;
    let totalPending = 0;

    const byProperty: Record<string, any> = {};
    const bySource: Record<string, number> = {};

    results.results?.forEach((row: any) => {
      const amount = row.total_amount || 0;
      totalRevenue += amount;

      if (row.status === 'received') {
        totalReceived += amount;
      } else if (row.status === 'pending') {
        totalPending += amount;
      }

      // By property
      if (!byProperty[row.property_id]) {
        byProperty[row.property_id] = {
          property_id: row.property_id,
          property_name: row.property_name,
          total: 0,
          received: 0,
          pending: 0,
        };
      }
      byProperty[row.property_id].total += amount;
      if (row.status === 'received') {
        byProperty[row.property_id].received += amount;
      } else if (row.status === 'pending') {
        byProperty[row.property_id].pending += amount;
      }

      // By source
      if (!bySource[row.source]) {
        bySource[row.source] = 0;
      }
      bySource[row.source] += amount;
    });

    return new Response(
      JSON.stringify({
        success: true,
        summary: {
          total_revenue: totalRevenue,
          total_received: totalReceived,
          total_pending: totalPending,
          by_property: Object.values(byProperty),
          by_source: bySource,
        },
        period: {
          start_date: startDate,
          end_date: endDate,
        },
      }),
      {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  } catch (error: any) {
    console.error('[Revenue Summary] Error:', error);
    return new Response(
      JSON.stringify({
        error: error.message || 'Failed to generate revenue summary',
      }),
      {
        status: error.message.includes('Unauthorized') ? 401 : 500,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
};
