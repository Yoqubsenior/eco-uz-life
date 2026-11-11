import Constants from "expo-constants";

/**
 * Where the Django API lives.
 *
 * 1. EXPO_PUBLIC_API_URL (from .env.local) wins — used for production builds.
 * 2. In development, reuse the host Metro is running on: Expo Go loaded this JS bundle
 *    from that machine, so the API (port 8000) is reachable there too. When your
 *    Wi-Fi/hotspot IP changes, nothing needs editing.
 *
 * ⚠️ EXPO_PUBLIC_* values are compiled INTO the app bundle. Anyone can read them by
 * unpacking the APK. Never put secrets (API tokens, passwords) in them.
 */
function devServerHost(): string | null {
  const hostUri = Constants.expoConfig?.hostUri; // e.g. "192.168.100.146:8081"
  return hostUri ? hostUri.split(":")[0] : null;
}

const host = devServerHost();

export const API_URL =
  process.env.EXPO_PUBLIC_API_URL ??
  (host ? `http://${host}:8000/api/v1` : "http://localhost:8000/api/v1");

export const REQUEST_TIMEOUT_MS = 15_000;
