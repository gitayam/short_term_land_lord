/**
 * POST/PUT/DELETE /api/guidebook/sections
 * Manage guidebook sections
 */

interface Env {
  DB: D1Database;
}

// POST - Create new section
export const onRequestPost: PagesFunction<Env> = async (context) => {
  const { env, request } = context;

  try {
    const body = await request.json();
    const {
      property_id,
      section_type,
      title,
      content,
      display_order,
      icon,
      is_published
    } = body;

    if (!property_id || !section_type || !title || !content) {
      return new Response(
        JSON.stringify({ error: 'Missing required fields' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const result = await env.DB.prepare(`
      INSERT INTO guidebook_sections (
        property_id, section_type, title, content,
        display_order, icon, is_published
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `).bind(
      property_id,
      section_type,
      title,
      content,
      display_order || 999,
      icon || '📄',
      is_published ? 1 : 0
    ).run();

    return new Response(
      JSON.stringify({
        success: true,
        id: result.meta.last_row_id,
        message: 'Section created successfully'
      }),
      { status: 201, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error creating section:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to create section', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};

// PUT - Update section
export const onRequestPut: PagesFunction<Env> = async (context) => {
  const { env, request } = context;

  try {
    const body = await request.json();
    const {
      id,
      section_type,
      title,
      content,
      display_order,
      icon,
      is_published
    } = body;

    if (!id) {
      return new Response(
        JSON.stringify({ error: 'Section ID required' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    await env.DB.prepare(`
      UPDATE guidebook_sections
      SET section_type = ?,
          title = ?,
          content = ?,
          display_order = ?,
          icon = ?,
          is_published = ?
      WHERE id = ?
    `).bind(
      section_type,
      title,
      content,
      display_order,
      icon,
      is_published ? 1 : 0,
      id
    ).run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Section updated successfully'
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error updating section:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to update section', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};

// DELETE - Delete section
export const onRequestDelete: PagesFunction<Env> = async (context) => {
  const { env, request } = context;
  const url = new URL(request.url);
  const id = url.searchParams.get('id');

  if (!id) {
    return new Response(
      JSON.stringify({ error: 'Section ID required' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  try {
    await env.DB.prepare(`
      DELETE FROM guidebook_sections WHERE id = ?
    `).bind(id).run();

    return new Response(
      JSON.stringify({
        success: true,
        message: 'Section deleted successfully'
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    console.error('Error deleting section:', err);
    return new Response(
      JSON.stringify({ error: 'Failed to delete section', details: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
};
