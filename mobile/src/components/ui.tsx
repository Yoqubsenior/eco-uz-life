import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

import { colors, radius, spacing } from "@/lib/theme";

type ButtonProps = {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: "primary" | "outline";
};

export function Button({
  title,
  onPress,
  loading = false,
  disabled = false,
  variant = "primary",
}: ButtonProps) {
  const outline = variant === "outline";
  const inactive = loading || disabled; // loading also blocks double submits
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: inactive, busy: loading }}
      onPress={onPress}
      disabled={inactive}
      style={({ pressed }) => [
        styles.button,
        outline ? styles.buttonOutline : styles.buttonPrimary,
        pressed && { opacity: 0.7 },
        inactive && { opacity: 0.45 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={outline ? colors.primary : "#fff"} />
      ) : (
        <Text style={[styles.buttonText, outline && { color: colors.primary }]}>{title}</Text>
      )}
    </Pressable>
  );
}

type FieldProps = TextInputProps & { label: string; error?: string };

export function Field({ label, error, style, ...inputProps }: FieldProps) {
  return (
    <View style={{ marginBottom: spacing.md }}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.muted}
        style={[styles.input, error ? { borderColor: colors.danger } : null, style]}
        {...inputProps}
      />
      {error ? <Text style={styles.fieldError}>{error}</Text> : null}
    </View>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <View style={styles.errorBanner}>
      <Text style={{ color: colors.danger }}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 50,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  buttonPrimary: { backgroundColor: colors.primary },
  buttonOutline: { borderWidth: 1.5, borderColor: colors.primary, backgroundColor: "transparent" },
  buttonText: { color: "#fff", fontSize: 16, fontWeight: "600" },
  label: { fontSize: 14, color: colors.muted, marginBottom: spacing.xs },
  input: {
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  fieldError: { color: colors.danger, marginTop: spacing.xs, fontSize: 13 },
  errorBanner: {
    backgroundColor: "#FDECEA",
    borderRadius: radius.sm,
    padding: spacing.md,
    marginBottom: spacing.md,
  },
});
