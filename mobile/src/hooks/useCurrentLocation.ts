import { useQuery } from "@tanstack/react-query";
import * as Location from "expo-location";

import { UserFacingError } from "@/lib/errors";

// Tashkent city centre — used when the user doesn't share their location.
export const TASHKENT_CENTER = { lat: 41.3111, lng: 69.2797 };

const GPS_TIMEOUT_MS = 8_000;

export type CurrentLocation = { lat: number; lng: number; isFallback: boolean };

/** Resolves to null instead of waiting forever. Indoors a fresh GPS fix can take minutes. */
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T | null> {
  return Promise.race([promise, new Promise<null>((resolve) => setTimeout(() => resolve(null), ms))]);
}

async function getLocation(): Promise<CurrentLocation> {
  const { granted } = await Location.requestForegroundPermissionsAsync();
  if (!granted) return { ...TASHKENT_CENTER, isFallback: true };

  // 1. A recent cached fix is instant and saves battery.
  // 2. Otherwise ask the GPS — but never wait more than 8 s for it.
  // 3. Still nothing (e.g. indoors): accept any last known position, however old.
  const position =
    (await Location.getLastKnownPositionAsync({ maxAge: 10 * 60_000 })) ??
    (await withTimeout(
      Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }),
      GPS_TIMEOUT_MS,
    )) ??
    (await Location.getLastKnownPositionAsync());

  if (!position) {
    throw new UserFacingError("Joylashuvni aniqlab bo'lmadi. Ochiq joyga chiqib qayta urining.");
  }
  return { lat: position.coords.latitude, lng: position.coords.longitude, isFallback: false };
}

export function useCurrentLocation() {
  return useQuery({ queryKey: ["location"], queryFn: getLocation, staleTime: 5 * 60_000 });
}
