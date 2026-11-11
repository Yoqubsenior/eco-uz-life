import { StyleSheet, Text, View } from "react-native";

import type { NearestStation, Pollutants } from "@/api/types";
import { formatDistance, readableTextColor, timeAgo } from "@/lib/format";
import { colors, radius, spacing } from "@/lib/theme";

const POLLUTANT_LABELS: Record<keyof Pollutants, string> = {
  pm25: "PM2.5",
  pm10: "PM10",
  no2: "NO₂",
  so2: "SO₂",
  co: "CO",
  o3: "O₃",
};

export function AqiCard({ station }: { station: NearestStation }) {
  const reading = station.latest;

  if (!reading) {
    return (
      <View style={styles.card}>
        <Text style={styles.stationName}>{station.name}</Text>
        <Text style={styles.muted}>Bu stansiyada hozircha ma'lumot yo'q.</Text>
      </View>
    );
  }

  const { category } = reading;
  const textColor = readableTextColor(category.color);
  const pollutants = (Object.keys(POLLUTANT_LABELS) as (keyof Pollutants)[]).filter(
    (key) => reading.pollutants[key] !== null,
  );

  return (
    <View style={styles.card}>
      <View
        style={[styles.badge, { backgroundColor: category.color }]}
        accessible
        accessibilityLabel={`Havo sifati indeksi ${reading.aqi}, ${category.label}`}
      >
        <Text style={[styles.aqi, { color: textColor }]}>{reading.aqi}</Text>
        <Text style={[styles.aqiUnit, { color: textColor }]}>AQI</Text>
      </View>
      <Text style={styles.label}>{category.label}</Text>

      <Text style={styles.stationName}>{station.name}</Text>
      <Text style={styles.muted}>
        {formatDistance(station.distance_m)} uzoqlikda · {timeAgo(reading.measured_at)}
      </Text>

      {reading.is_stale ? (
        <View style={styles.staleBanner}>
          <Text style={{ color: colors.warningText }}>
            ⚠️ Ma'lumot eskirgan bo'lishi mumkin (3 soatdan oldin o'lchangan).
          </Text>
        </View>
      ) : null}

      <View style={styles.adviceBox}>
        <Text style={styles.adviceTitle}>Tavsiya</Text>
        <Text style={styles.adviceText}>{category.advice}</Text>
        <Text style={[styles.adviceTitle, { marginTop: spacing.sm }]}>
          Bolalar, keksalar va sezgir guruhlar uchun
        </Text>
        <Text style={styles.adviceText}>{category.sensitive_advice}</Text>
      </View>

      {pollutants.length > 0 ? (
        <View style={styles.pollutants}>
          {pollutants.map((key) => (
            <View key={key} style={styles.pollutant}>
              <Text style={styles.pollutantValue}>{Math.round(reading.pollutants[key] ?? 0)}</Text>
              <Text style={styles.muted}>{POLLUTANT_LABELS[key]}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {/* Required by the WAQI terms of use. */}
      <Text style={styles.attribution}>Ma'lumot manbai: {station.source}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: spacing.lg,
    alignItems: "center",
  },
  badge: {
    width: 150,
    height: 150,
    borderRadius: 75,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.md,
  },
  aqi: { fontSize: 56, fontWeight: "800" },
  aqiUnit: { fontSize: 14, fontWeight: "600", marginTop: -6 },
  label: { fontSize: 22, fontWeight: "700", color: colors.text, marginBottom: spacing.md },
  stationName: { fontSize: 16, fontWeight: "600", color: colors.text, textAlign: "center" },
  muted: { color: colors.muted, fontSize: 13, textAlign: "center", marginTop: 2 },
  staleBanner: {
    backgroundColor: colors.warningBg,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginTop: spacing.md,
    alignSelf: "stretch",
  },
  adviceBox: {
    alignSelf: "stretch",
    backgroundColor: colors.background,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  adviceTitle: { fontWeight: "700", color: colors.text, marginBottom: 2 },
  adviceText: { color: colors.text, lineHeight: 20 },
  pollutants: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  pollutant: {
    minWidth: 80,
    alignItems: "center",
    padding: spacing.sm,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
  },
  pollutantValue: { fontSize: 18, fontWeight: "700", color: colors.text },
  attribution: { color: colors.muted, fontSize: 11, marginTop: spacing.md },
});
