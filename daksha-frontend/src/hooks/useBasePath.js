import { useLocation } from 'react-router-dom';

/**
 * Returns the base path for the current context:
 *   '/kiosk' when the user is inside the kiosk module
 *   '/dash'  everywhere else (user web app)
 *
 * Use this in shared pages (ChatInterface, ChatsPage, OrdersPage, etc.)
 * so they navigate correctly whether rendered in the kiosk or web app.
 *
 * @returns {{ basePath: string, isKiosk: boolean }}
 */
export function useBasePath() {
  const { pathname } = useLocation();
  const isKiosk = pathname.startsWith('/kiosk');
  return { basePath: isKiosk ? '/kiosk' : '/dash', isKiosk };
}
