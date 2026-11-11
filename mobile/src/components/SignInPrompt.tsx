import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "@/lib/theme";

import { Button } from "./ui";

/** Shown on screens that need an account, instead of the screen's content. */
export function SignInPrompt({ message }: { message: string }) {
  return (
    <View style={styles.container}>
      <Text style={styles.text}>{message}</Text>
      <Button title="Kirish" onPress={() => router.push("/login")} />
      <Button title="Ro'yxatdan o'tish" variant="outline" onPress={() => router.push("/register")} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: spacing.lg, gap: spacing.sm },
  text: { textAlign: "center", color: colors.muted, fontSize: 16, marginBottom: spacing.md },
});
