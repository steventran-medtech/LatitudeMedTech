// SOC II CC6.6 — Centralised session-token management for all API calls.
// Call setToken() once on app init with the value from GET /api/auth/token.
// Spread authHdr() into headers for every mutating (POST/DELETE) request.
// Use wsUrl() to attach the token as a query-param on WebSocket upgrades.

let _token = '';

export function setToken(tok) { _token = tok || ''; }
export function getToken()    { return _token; }

/** Returns { 'X-Athena-Key': <token> } — spread into fetch() headers. */
export function authHdr() {
  return _token ? { 'X-Athena-Key': _token } : {};
}

/** Prefixes a WebSocket path with ?token=<token> for server-side auth. */
export function wsUrl(path) {
  return _token ? `${path}?token=${encodeURIComponent(_token)}` : path;
}
