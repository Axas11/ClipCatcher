/* Helpers de autenticacion: persistencia del JWT en localStorage y
 * proteccion de paginas que requieren sesion. */

const TOKEN_KEY = 'clipcatcher.token';

export function saveToken(token) {
  if (!token) return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

/* Cierra la sesion y vuelve a la pantalla de login. */
export function logout() {
  clearToken();
  // Solo redirige si no estamos ya ahi, para no entrar en bucle.
  if (!location.pathname.endsWith('/index.html') && location.pathname !== '/') {
    location.replace('index.html');
  }
}

/* Llamar al inicio de cualquier pagina protegida. Si no hay token guardado
 * redirige a `index.html`. Devuelve true si hay sesion para que el script
 * pueda decidir si seguir cargando datos. */
export function requireAuth() {
  const token = getToken();
  if (!token) {
    location.replace('index.html');
    return false;
  }
  return true;
}
