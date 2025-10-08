/**
 * Authentication Utilities
 * Password hashing, JWT generation, session management
 */

import * as bcrypt from 'bcryptjs';
import { Env } from '../_middleware';

const SALT_ROUNDS = 10;

/**
 * Hash a plain text password
 */
export async function hashPassword(password: string): Promise<string> {
  return await bcrypt.hash(password, SALT_ROUNDS);
}

/**
 * Verify password against hash
 */
export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return await bcrypt.compare(password, hash);
}

/**
 * Generate a simple JWT-like session token
 * For production, consider using @tsndr/cloudflare-worker-jwt
 */
export function generateSessionToken(): string {
  return crypto.randomUUID();
}

/**
 * Get user from session token
 * Checks KV first (fast), then falls back to D1
 */
export async function getUserFromToken(token: string, env: Env): Promise<any> {
  if (!token) {
    throw new Error('No token provided');
  }

  // Try KV first (faster)
  let sessionData = await env.KV.get(`session:${token}`, { type: 'json' });

  // Fallback to D1 if not in KV
  if (!sessionData) {
    const session = await env.DB.prepare(
      'SELECT user_data FROM session_cache WHERE session_token = ? AND datetime(expires_at) > datetime("now")'
    )
      .bind(token)
      .first();

    if (session) {
      sessionData = JSON.parse(session.user_data as string);
      // Restore to KV for future requests
      await env.KV.put(`session:${token}`, JSON.stringify(sessionData), {
        expirationTtl: 86400,
      });
    }
  }

  if (!sessionData) {
    throw new Error('Invalid or expired session');
  }

  return sessionData;
}

/**
 * Extract token from Authorization header
 */
export function extractToken(request: Request): string {
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    throw new Error('Missing or invalid Authorization header');
  }
  return authHeader.substring(7);
}

/**
 * Require authentication middleware
 * Use this in endpoints that need authentication
 */
export async function requireAuth(request: Request, env: Env): Promise<any> {
  try {
    const token = extractToken(request);
    const user = await getUserFromToken(token, env);
    return user;
  } catch (error: any) {
    throw new Error('Unauthorized: ' + error.message);
  }
}

/**
 * Create a new session for user
 */
export async function createSession(user: any, env: Env): Promise<string> {
  const sessionToken = generateSessionToken();

  const sessionData = {
    userId: user.id,
    email: user.email,
    role: user.role,
    firstName: user.first_name,
    lastName: user.last_name,
    createdAt: new Date().toISOString(),
  };

  // Store in KV (expires in 24 hours)
  await env.KV.put(`session:${sessionToken}`, JSON.stringify(sessionData), {
    expirationTtl: 86400,
  });

  // Also store in D1 for persistence
  await env.DB.prepare(
    `INSERT INTO session_cache (session_token, user_id, user_data, expires_at)
     VALUES (?, ?, ?, datetime('now', '+1 day'))`
  )
    .bind(sessionToken, user.id, JSON.stringify(sessionData))
    .run();

  return sessionToken;
}

/**
 * Destroy a session (logout)
 */
export async function destroySession(token: string, env: Env): Promise<void> {
  // Remove from KV
  await env.KV.delete(`session:${token}`);

  // Remove from D1
  await env.DB.prepare('DELETE FROM session_cache WHERE session_token = ?')
    .bind(token)
    .run();
}

/**
 * Validate password strength
 */
export function validatePassword(password: string): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Password must be at least 8 characters long');
  }

  if (!/[A-Z]/.test(password)) {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (!/[a-z]/.test(password)) {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (!/[0-9]/.test(password)) {
    errors.push('Password must contain at least one number');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate email format
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Check if user has required role
 * Roles hierarchy: admin > property_owner > property_manager > service_staff > tenant > property_guest
 */
export function hasRole(userRole: string, requiredRole: string): boolean {
  const roleHierarchy: { [key: string]: number } = {
    'admin': 6,
    'property_owner': 5,
    'property_manager': 4,
    'service_staff': 3,
    'tenant': 2,
    'property_guest': 1,
  };

  const userLevel = roleHierarchy[userRole] || 0;
  const requiredLevel = roleHierarchy[requiredRole] || 0;

  return userLevel >= requiredLevel;
}

/**
 * Require specific role middleware
 * Use this to protect endpoints that need specific roles
 */
export async function requireRole(request: Request, env: Env, requiredRole: string): Promise<any> {
  const user = await requireAuth(request, env);

  if (!hasRole(user.role, requiredRole)) {
    throw new Error(`Forbidden: ${requiredRole} role required`);
  }

  return user;
}

/**
 * Check if user is admin
 */
export async function requireAdmin(request: Request, env: Env): Promise<any> {
  return await requireRole(request, env, 'admin');
}

/**
 * Check if user is property owner or admin
 */
export async function requireOwner(request: Request, env: Env): Promise<any> {
  return await requireRole(request, env, 'property_owner');
}
