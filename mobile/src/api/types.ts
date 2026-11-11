// Shapes of API responses — mirror docs/04-api.md (the backend/mobile contract).

export type User = {
  id: number;
  email: string;
  display_name: string;
  district: number | null;
  district_name: string | null;
  date_joined: string;
};

export type AqiCategory = {
  key: string;
  label: string;
  color: string;
  advice: string;
  sensitive_advice: string;
};

export type Pollutants = Record<"pm25" | "pm10" | "no2" | "so2" | "co" | "o3", number | null>;

export type Reading = {
  measured_at: string;
  aqi: number;
  category: AqiCategory;
  pollutants: Pollutants;
  is_stale: boolean;
};

export type Station = {
  id: number;
  name: string;
  source: string;
  lat: number;
  lng: number;
  district: string | null;
  latest: Reading | null;
};

export type NearestStation = Station & { distance_m: number };

export type PointsSummary = {
  balance: number;
  transactions: { amount: number; reason: string; reason_display: string; created_at: string }[];
};
