import { router } from "expo-router";
import { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text } from "react-native";

import { useAuth } from "@/auth/AuthProvider";
import { Button, ErrorBanner, Field } from "@/components/ui";
import { errorMessage, fieldErrors, type FieldErrors } from "@/lib/errors";
import { colors, spacing } from "@/lib/theme";

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    setErrors({});
    setBanner(null);
    try {
      await signUp({ email: email.trim(), password, display_name: displayName.trim() });
      router.back();
    } catch (e) {
      // The backend attaches errors to fields ({"password": [...]}) — shown under each input.
      const byField = fieldErrors(e);
      if (Object.keys(byField).length) setErrors(byField);
      else setBanner(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
        {banner ? <ErrorBanner message={banner} /> : null}
        <Field
          label="Ism (reytingda ko'rinadi)"
          value={displayName}
          onChangeText={setDisplayName}
          maxLength={60}
          error={errors.display_name}
        />
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          error={errors.email}
        />
        <Field
          label="Parol (kamida 8 belgi)"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoComplete="new-password"
          textContentType="newPassword"
          error={errors.password}
        />
        <Button title="Ro'yxatdan o'tish" onPress={submit} loading={loading} />
        <Text style={styles.link} onPress={() => router.replace("/login")}>
          Hisobingiz bormi? Kirish
        </Text>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.lg },
  link: { color: colors.primary, textAlign: "center", marginTop: spacing.lg, fontWeight: "600" },
});
