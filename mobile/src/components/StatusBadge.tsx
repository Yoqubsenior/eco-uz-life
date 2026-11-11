import { StyleSheet, Text, View } from "react-native";

import type { ReportStatus } from "@/api/types";
import { STATUS_COLORS, STATUS_LABELS } from "@/lib/reportMeta";

export function StatusBadge({ status }: { status: ReportStatus }) {
  return (
    <View style={[styles.badge, { backgroundColor: STATUS_COLORS[status] }]}>
      <Text style={styles.text}>{STATUS_LABELS[status]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, alignSelf: "flex-start" },
  text: { color: "#fff", fontSize: 12, fontWeight: "700" },
});
