import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from "react-native";

import { airApi } from "@/api/endpoints";
import { AqiCard } from "@/components/AqiCard";
import { Button, ErrorBanner } from "@/components/ui";
import { useCurrentLocation } from "@/hooks/useCurrentLocation";
import { errorMessage } from "@/lib/errors";
import { colors, spacing } from "@/lib/theme";

/** Air quality at the nearest station. Public: works without an account. [US-2] */
export default function AirScreen() {
  const location = useCurrentLocation();
  const coords = location.data;

  const nearest = useQuery({
    queryKey: ["air", "nearest", coords?.lat, coords?.lng],
    queryFn: () => airApi.nearest(coords!.lat, coords!.lng),
    enabled: !!coords, // dependent query: wait for the location first
  });

  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = async () => {
    setRefreshing(true);
    await location.refetch();
    await nearest.refetch();
    setRefreshing(false);
  };

  const error = location.error ?? nearest.error;

  return (
    <ScrollView
      contentContainerStyle={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {coords?.isFallback ? (
        <Text style={styles.note}>
          Joylashuvga ruxsat berilmadi — Toshkent markaziga eng yaqin stansiya ko'rsatilmoqda.
        </Text>
      ) : null}

      {error ? (
        <View>
          <ErrorBanner message={errorMessage(error)} />
          <Button title="Qayta urinish" onPress={onRefresh} />
        </View>
      ) : nearest.data ? (
        <AqiCard station={nearest.data} />
      ) : (
        <View style={styles.loading}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.note}>
            {coords ? "Havo sifati yuklanmoqda..." : "Joylashuv aniqlanmoqda..."}
          </Text>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, flexGrow: 1 },
  loading: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md },
  note: { color: colors.muted, textAlign: "center", marginBottom: spacing.md },
});
