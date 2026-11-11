import { router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from "react-native";

import { useAuth } from "@/auth/AuthProvider";
import { Button, ErrorBanner, Field } from "@/components/ui";
import { errorMessage } from "@/lib/errors";
import { colors, spacing } from "@/lib/theme";

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!email || !password) {
      setError("Email va parolni kiriting.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await signIn(email, password);
      router.back();
    } catch (e) {
      setError(errorMessage(e)); // 401 -> "Email yoki parol noto'g'ri." (no hint which one)
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {error ? <ErrorBanner message={error} /> : null}
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          textContentType="emailAddress"
        />
        <Field
          label="Parol"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="current-password"
          textContentType="password"
          onSubmitEditing={submit}
        />
        <Button title="Kirish" onPress={submit} loading={loading} />
        <Text style={styles.link} onPress={() => router.replace("/register")}>
          Hisobingiz yo'qmi? Ro'yxatdan o'ting
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg },
  link: { color: colors.primary, textAlign: "center", marginTop: spacing.lg, fontWeight: "600" },
});
