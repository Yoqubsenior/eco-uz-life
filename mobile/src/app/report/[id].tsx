import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { router, Stack, useLocalSearchParams } from "expo-router";
import { ActivityIndicator, Alert, Image, ScrollView, StyleSheet, Text, View } from "react-native";

import { reportsApi } from "@/api/endpoints";
import { StatusBadge } from "@/components/StatusBadge";
import { Button, ErrorBanner } from "@/components/ui";
import { errorMessage } from "@/lib/errors";
import { timeAgo } from "@/lib/format";
import { STATUS_LABELS } from "@/lib/reportMeta";
import { colors, radius, spacing } from "@/lib/theme";

/** One report: photos, status, history. The author can delete it while it's `new`. [FR-R3, FR-R7] */
export default function ReportDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const queryClient = useQueryClient();
  const report = useQuery({ queryKey: ["reports", "detail", id], queryFn: () => reportsApi.detail(id) });

  const remove = useMutation({
    mutationFn: () => reportsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      router.back();
    },
  });

  const confirmDelete = () =>
    Alert.alert("Murojaatni o'chirish", "Haqiqatan ham o'chirmoqchimisiz? Buni qaytarib bo'lmaydi.", [
      { text: "Bekor qilish", style: "cancel" },
      { text: "O'chirish", style: "destructive", onPress: () => remove.mutate() },
    ]);

  if (report.isLoading) {
    return <ActivityIndicator style={{ marginTop: spacing.xl }} color={colors.primary} />;
  }
  if (report.error || !report.data) {
    // 404 also covers "exists but you may not see it" — the API doesn't reveal which.
    return (
      <View style={{ padding: spacing.md }}>
        <ErrorBanner message={errorMessage(report.error)} />
      </View>
    );
  }

  const data = report.data;
  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: data.category.name_uz }} />

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: spacing.sm }}>
        {data.photos.map((photo) => (
          <Image
            key={photo.url}
            source={{ uri: photo.url }}
            style={[styles.photo, { aspectRatio: photo.width / photo.height }]}
          />
        ))}
      </ScrollView>

      <View style={styles.card}>
        <StatusBadge status={data.status} />
        {data.rejection_reason ? (
          <Text style={styles.rejected}>Sabab: {data.rejection_reason}</Text>
        ) : null}
        {data.duplicate_of ? (
          <Text style={styles.muted}>Bu joyda shunday muammo avval bildirilgan — birlashtirildi.</Text>
        ) : null}
        {data.description ? <Text style={styles.description}>{data.description}</Text> : null}
        <Text style={styles.muted}>
          {data.district ? `📍 ${data.district} · ` : "📍 "}
          {data.lat.toFixed(5)}, {data.lng.toFixed(5)}
        </Text>
        <Text style={styles.muted}>
          {data.author_name} · {timeAgo(data.created_at)}
        </Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.heading}>Holat tarixi</Text>
        {data.history.map((entry, index) => (
          <View key={`${entry.to_status}-${index}`} style={styles.historyRow}>
            <View style={styles.dot} />
            <Text style={{ flex: 1, color: colors.text }}>{STATUS_LABELS[entry.to_status]}</Text>
            <Text style={styles.muted}>{timeAgo(entry.created_at)}</Text>
          </View>
        ))}
      </View>

      {data.is_mine && data.status === "new" ? (
        <>
          {remove.error ? <ErrorBanner message={errorMessage(remove.error)} /> : null}
          <Button
            title="Murojaatni o'chirish"
            variant="outline"
            onPress={confirmDelete}
            loading={remove.isPending}
          />
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, gap: spacing.md },
  photo: { height: 220, borderRadius: radius.md, backgroundColor: colors.border },
  card: { backgroundColor: colors.card, borderRadius: radius.lg, padding: spacing.md, gap: spacing.sm },
  heading: { fontWeight: "700", fontSize: 16, color: colors.text },
  description: { color: colors.text, fontSize: 15, lineHeight: 21 },
  rejected: { color: colors.danger, fontWeight: "600" },
  muted: { color: colors.muted, fontSize: 13 },
  historyRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  dot: { width: 10, height: 10, borderRadius: 5, backgroundColor: colors.primary },
});
