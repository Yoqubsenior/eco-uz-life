import * as SecureStore from "expo-secure-store";

/**
 * JWT storage. SecureStore = Android Keystore (encrypted, per-app).
 * NOT AsyncStorage: that is plain text on disk, readable on rooted devices and in backups.
 */
const ACCESS_KEY = "eco.access";
const REFRESH_KEY = "eco.refresh";

export type Tokens = { access: string; refresh: string };

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_KEY);
}

export async function saveTokens({ access, refresh }: Tokens): Promise<void> {
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, access),
    SecureStore.setItemAsync(REFRESH_KEY, refresh),
  ]);
}

export async function clearTokens(): Promise<void> {
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
  ]);
}
