import Ionicons from "@expo/vector-icons/Ionicons";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { FlatList, Image, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";

import { reportsApi } from "@/api/endpoints";
import { useAuth } from "@/auth/AuthProvider";
import { SignInPrompt } from "@/components/SignInPrompt";
import { StatusBadge } from "@/components/StatusBadge";
import { ErrorBanner } from "@/components/ui";
import { errorMessage } from "@/lib/errors";
import { timeAgo } from "@/lib/format";
import { categoryIcon } from "@/lib/reportMeta";
import { colors, radius, spacing } from "@/lib/theme";

/** The user's own reports, every status. [FR-R4] */
export default function MyReportsScreen() {
  const { status } = useAuth();
  if (status !== "signedIn") {
    return <SignInPrompt message="Murojaatlaringizni ko'rish uchun hisobingizga kiring." />;
  }
  return <MyReportsList />;
}

function MyReportsList() {
  const reports = useQuery({ queryKey: ["reports", "mine"], queryFn: reportsApi.mine });
  // Cached from the "new report" screen — gives slug -> human name without another request.
  const categories = useQuery({ queryKey: ["categories"], queryFn: reportsApi.categories });
  const names = Object.fromEntries((categories.data ?? []).map((c) => [c.slug, c.name_uz]));

  return (
    <FlatList
      data={reports.data ?? []}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.list}
      refreshControl={
        // Braces matter: `() => reports.refetch()` would return the query result,
        // but onRefresh must return void.
        <RefreshControl
          refreshing={reports.isRefetching}
          onRefresh={() => {
            reports.refetch();
          }}
        />
      }
      // FlatList's types accept `undefined` (not `null`) for "no component".
      ListHeaderComponent={
        reports.error ? <ErrorBanner message={errorMessage(reports.error)} /> : undefined
      }
      ListEmptyComponent={
        reports.isLoading ? undefined : (
          <Text style={styles.empty}>
            Hali murojaat yubormagansiz. "Yuborish" bo'limidan birinchi murojaatingizni yuboring 🌱
          </Text>
        )
      }
      renderItem={({ item }) => (
        <Pressable
          style={styles.row}
          onPress={() => router.push({ pathname: "/report/[id]", params: { id: item.id } })}
        >
          {item.thumbnail ? (
            <Image source={{ uri: item.thumbnail }} style={styles.thumb} />
          ) : (
            <View style={[styles.thumb, styles.thumbPlaceholder]}>
              <Ionicons name={categoryIcon(item.category)} size={28} color={colors.muted} />
            </View>
          )}
          <View style={{ flex: 1, gap: 4 }}>
            <Text style={styles.title}>{names[item.category] ?? item.category}</Text>
            <StatusBadge status={item.status} />
            <Text style={styles.muted}>{timeAgo(item.created_at)}</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={colors.muted} />
        </Pressable>
      )}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: spacing.md, gap: spacing.sm, flexGrow: 1 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.card,
    borderRadius: radius.md,
    padding: spacing.sm,
  },
  thumb: { width: 72, height: 72, borderRadius: radius.sm },
  thumbPlaceholder: { backgroundColor: colors.background, alignItems: "center", justifyContent: "center" },
  title: { fontWeight: "700", color: colors.text },
  muted: { color: colors.muted, fontSize: 12 },
  empty: { textAlign: "center", color: colors.muted, marginTop: spacing.xl, paddingHorizontal: spacing.lg },
});
