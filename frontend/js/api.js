/* Cliente HTTP minimo de ClipCatcher.
 *
 * Envuelve `fetch` para anadir automaticamente el header Authorization con
 * el JWT guardado por `auth.js`, y centraliza el manejo de 401 (sesion
 * expirada -> logout). Las funciones devuelven el JSON parseado o lanzan
 * `ApiError` con el status y detail del backend.
 */

import { getToken, logout } from './auth.js';

export const API_BASE = '/api';

export class ApiError extends Error {
  constructor(status, detail, body = null) {
    super(detail || `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
    this.body = body;
  }
}

async function _request(path, opts = {}) {
  const { json, skipAuth, ...rest } = opts;
  const headers = { ...(rest.headers || {}) };
  let body = rest.body;
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  }
  if (!skipAuth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(API_BASE + path, { ...rest, headers, body });
  if (res.status === 401 && !skipAuth) {
    logout();
    throw new ApiError(401, 'sesion expirada');
  }
  if (!res.ok) {
    let parsed = null;
    try { parsed = await res.json(); } catch (_) { /* respuesta sin body */ }
    throw new ApiError(res.status, parsed?.detail || res.statusText, parsed);
  }
  return res;
}

/* ----------------------- Autenticacion ----------------------- */

export async function register({ email, password, name }) {
  const res = await _request('/auth/register', {
    method: 'POST',
    json: { email, password, name },
    skipAuth: true,
  });
  return res.json();
}

export async function login({ email, password }) {
  // OAuth2 password flow: form-encoded `username` + `password`.
  const body = new URLSearchParams({ username: email, password });
  const res = await _request('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
    skipAuth: true,
  });
  return res.json();
}

export async function getMe() {
  const res = await _request('/users/me');
  return res.json();
}

/* F8: indica si el backend tiene credenciales de Google OAuth
 * configuradas. El frontend usa esto para decidir si pintar el boton
 * "Continuar con Google" o no (degradacion elegante). */
export async function googleAuthAvailable() {
  const res = await _request('/auth/google/available', { skipAuth: true });
  const body = await res.json();
  return Boolean(body && body.available);
}

/* F12: agregados anonimos para la landing publica (sin auth). */
export async function getGlobalStats() {
  const res = await _request('/stats/global', { skipAuth: true });
  return res.json();
}

/* F12.2: timeline de eventos recientes del usuario actual. */
export async function getMyActivity() {
  const res = await _request('/users/me/activity');
  return res.json();
}

export async function getMyStats() {
  const res = await _request('/users/me/stats');
  return res.json();
}

/* F11: actualiza nombre y/o email del usuario actual. Solo se envian
 * los campos definidos en `payload`. Devuelve UserOut. */
export async function updateMyProfile(payload) {
  const res = await _request('/users/me', { method: 'PATCH', json: payload });
  return res.json();
}

/* F11: cambia la contraseña. 204 sin body en exito; 401 si current
 * no coincide; 403 si la cuenta es Google; 422 si new_password < 8. */
export async function changeMyPassword(currentPassword, newPassword) {
  await _request('/users/me/password', {
    method: 'PUT',
    json: { current_password: currentPassword, new_password: newPassword },
  });
  return true;
}

export async function getMySettings() {
  const res = await _request('/users/me/settings');
  return res.json();
}

export async function updateMySettings(payload) {
  const res = await _request('/users/me/settings', {
    method: 'PUT',
    json: payload,
  });
  return res.json();
}

/* ----------------------- Videos ----------------------- */

export async function listVideos() {
  const res = await _request('/videos');
  return res.json();
}

export async function getVideo(videoId) {
  const res = await _request(`/videos/${videoId}`);
  return res.json();
}

export async function deleteVideo(videoId) {
  // 204 No Content: no hay body; resolver a true.
  await _request(`/videos/${videoId}`, { method: 'DELETE' });
  return true;
}

/* Sube un video. `onProgress` recibe un valor entre 0 y 1. Usa
 * XMLHttpRequest porque `fetch` aun no expone el progreso de subida en
 * todos los navegadores. `overrides` (F10.2) es un objeto opcional con
 * `chain_window_seconds`, `clip_margin_seconds`, `clip_duration_seconds`;
 * solo se anaden los campos no nulos al FormData (asi el backend trata
 * NULL como "no override" y cae a defaults del usuario).
 * `convertTiktok` (F13.2.4): si true, el processor genera variante 9:16. */
export function uploadVideo(file, onProgress, overrides = null, convertTiktok = false) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const fd = new FormData();
    fd.append('file', file);
    if (overrides) {
      for (const k of ['chain_window_seconds', 'clip_margin_seconds', 'clip_duration_seconds']) {
        if (overrides[k] != null) fd.append(k, String(overrides[k]));
      }
    }
    // Solo enviamos el flag si esta activo; el backend tiene default
    // False, asi un upload sin checkbox se comporta como antes.
    if (convertTiktok) fd.append('convert_to_tiktok', 'true');
    xhr.open('POST', API_BASE + '/videos');
    const token = getToken();
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && typeof onProgress === 'function') {
        onProgress(e.loaded / e.total);
      }
    };
    xhr.onload = () => {
      const ok = xhr.status >= 200 && xhr.status < 300;
      let parsed = null;
      try { parsed = JSON.parse(xhr.responseText); } catch (_) { /* sin body */ }
      if (ok) return resolve(parsed);
      if (xhr.status === 401) logout();
      reject(new ApiError(xhr.status, parsed?.detail || xhr.statusText, parsed));
    };
    xhr.onerror = () => reject(new ApiError(0, 'error de red'));
    xhr.send(fd);
  });
}

/* ----------------------- Clips ----------------------- */

/* Descarga un clip como blob y devuelve un object URL utilizable como
 * `src` de `<video>` o `href` de descarga. El llamante debe liberar la
 * URL con `URL.revokeObjectURL` cuando ya no la necesite.
 *
 * No podemos usar `<video src="/api/...">` directamente porque el
 * elemento `<video>` no envia el header `Authorization`. Para un MVP
 * con clips pequenos (~12 MB) este tradeoff es aceptable.
 */
export async function fetchClipBlobUrl(clipId, mode = 'stream') {
  // Modos validos: stream (inline), download (16:9 con attachment),
  // tiktok (variante 9:16 F13.2 con attachment).
  if (mode !== 'stream' && mode !== 'download' && mode !== 'tiktok') {
    throw new Error(`mode invalido: ${mode}`);
  }
  const res = await _request(`/clips/${clipId}/${mode}`);
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}
