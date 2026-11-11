import { useQuery } from "@tanstack/react-query";
import * as Location from "expo-location";

// Tashkent city centre — used when the user doesn't share their location.
export const TASHKENT_CENTER = { lat: 41.3111, lng: 69.2797 };

export type CurrentLocation = { lat: number; lng: number; isFallback: boolean };

async function getLocation(): Promise<CurrentLocation> {
  const { granted } = await Location.requestForegroundPermissionsAsync();
  if (!granted) return { ...TASHKENT_CENTER, isFallback: true };

  // A recent cached fix is instant and saves battery; ask the GPS only if there is none.
  const position =
    (await Location.getLastKnownPositionAsync({ maxAge: 10 * 60_000 })) ??
    (await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }));

  return { lat: position.coords.latitude, lng: position.coords.longitude, isFallback: false };
}

export function useCurrentLocation() {
  return useQuery({ queryKey: ["location"], queryFn: getLocation, staleTime: 5 * 60_000 });
}
