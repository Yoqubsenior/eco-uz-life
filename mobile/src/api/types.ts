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

// ---------- Reports ----------

export type ReportStatus = "new" | "verified" | "in_progress" | "resolved" | "rejected";

export type Category = { slug: string; name_uz: string; icon: string };

export type ReportDetail = {
  id: string;
  category: Category;
  description: string;
  status: ReportStatus;
  status_display: string;
  rejection_reason: string | null; // only sent to the author
  lat: number;
  lng: number;
  district: string | null;
  author_name: string;
  is_mine: boolean;
  duplicate_of: string | null;
  photos: { url: string; width: number; height: number }[];
  history: { to_status: ReportStatus; created_at: string }[];
  created_at: string;
};

export type MyReport = {
  id: string;
  category: string; // slug
  status: ReportStatus;
  status_display: string;
  thumbnail: string | null;
  created_at: string;
};
