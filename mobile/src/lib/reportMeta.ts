import type Ionicons from "@expo/vector-icons/Ionicons";

import type { ReportStatus } from "@/api/types";

type IconName = keyof typeof Ionicons.glyphMap;

/** Status colours used for badges and (later) map markers. */
export const STATUS_COLORS: Record<ReportStatus, string> = {
  new: "#6B7280", // grey: waiting for a moderator
  verified: "#1D6FD8", // blue
  in_progress: "#E08A00", // orange
  resolved: "#1B7F4B", // green
  rejected: "#C62828", // red
};

export const STATUS_LABELS: Record<ReportStatus, string> = {
  new: "Yangi",
  verified: "Tasdiqlangan",
  in_progress: "Jarayonda",
  resolved: "Hal qilindi",
  rejected: "Rad etildi",
};

// The backend stores generic icon names; the app maps category slugs to its own icon set.
const CATEGORY_ICONS: Record<string, IconName> = {
  "illegal-dump": "trash-outline",
  "tree-damage": "leaf-outline",
  "air-pollution": "flame-outline",
  water: "water-outline",
};

export function categoryIcon(slug: string): IconName {
  return CATEGORY_ICONS[slug] ?? "alert-circle-outline";
}
