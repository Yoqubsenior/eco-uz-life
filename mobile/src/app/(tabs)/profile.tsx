import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { pointsApi } from "@/api/endpoints";
import { useAuth } from "@/auth/AuthProvider";
import { Button } from "@/components/ui";
import { colors, radius, spacing } from "@/lib/theme";

export default function ProfileScreen() {
  const { status, user, signOut } = useAuth();

  const points = useQuery({
    queryKey: ["points", "me"],
    queryFn: pointsApi.mine,
    enabled: status === "signedIn",
  });

  if (status !== "signedIn" || !user) {
    return (
      <View style={styles.center}>
        <Text style={styles.title}>Eco UZ Life'ga xush kelibsiz 🌿</Text>
        <Text style={styles.muted}>
          Murojaat yuborish va Eco Ball to'plash uchun hisobingizga kiring.
        </Text>
        <View style={styles.actions}>
          <Button title="Kirish" onPress={() => router.push("/login")} />
          <Button
            title="Ro'yxatdan o'tish"
            variant="outline"
            onPress={() => router.push("/register")}
          />
        </View>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.card}>
        <Text style={styles.title}>{user.display_name || "Foydalanuvchi"}</Text>
        <Text style={styles.muted}>{user.email}</Text>
        {user.district_name ? <Text style={styles.muted}>📍 {user.district_name}</Text> : null}
      </View>

      <View style={[styles.card, { alignItems: "center" }]}>
        <Text style={styles.muted}>Eco Ball</Text>
        <Text style={styles.points}>{points.data?.balance ?? "—"}</Text>
        <Text style={styles.muted}>Tasdiqlangan murojaat +10 · hal qilingan +5</Text>
      </View>

      <Button title="Chiqish" variant="outline" onPress={signOut} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, gap: spacing.md },
  center: { flex: 1, justifyContent: "center", padding: spacing.lg },
  actions: { gap: spacing.sm, marginTop: spacing.lg },
  card: { backgroundColor: colors.card, borderRadius: radius.lg, padding: spacing.lg, gap: 4 },
  title: { fontSize: 22, fontWeight: "700", color: colors.text, textAlign: "center" },
  muted: { color: colors.muted, textAlign: "center" },
  points: { fontSize: 48, fontWeight: "800", color: colors.primary },
});
