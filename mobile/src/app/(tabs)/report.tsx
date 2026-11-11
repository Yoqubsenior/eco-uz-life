import Ionicons from "@expo/vector-icons/Ionicons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { File } from "expo-file-system";
import { router } from "expo-router";
import { useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { reportsApi } from "@/api/endpoints";
import { useAuth } from "@/auth/AuthProvider";
import { PhotoPicker, type PickedPhoto } from "@/components/PhotoPicker";
import { SignInPrompt } from "@/components/SignInPrompt";
import { Button, ErrorBanner, Field } from "@/components/ui";
import { useCurrentLocation } from "@/hooks/useCurrentLocation";
import { errorMessage, fieldErrors } from "@/lib/errors";
import { categoryIcon } from "@/lib/reportMeta";
import { colors, radius, spacing } from "@/lib/theme";

/** New report: category + 1-3 photos + GPS location + optional description. [FR-R1, US-1] */
export default function NewReportScreen() {
  const { status } = useAuth();
  if (status !== "signedIn") {
    return <SignInPrompt message="Murojaat yuborish uchun hisobingizga kiring." />;
  }
  return <NewReportForm />;
}

function NewReportForm() {
  const queryClient = useQueryClient();
  const categories = useQuery({ queryKey: ["categories"], queryFn: reportsApi.categories });
  const location = useCurrentLocation();

  const [category, setCategory] = useState<string | null>(null);
  const [photos, setPhotos] = useState<PickedPhoto[]>([]);
  const [description, setDescription] = useState("");

  const create = useMutation({
    mutationFn: () => {
      const coords = location.data!;
      const form = new FormData();
      form.append("category", category!);
      form.append("lat", String(coords.lat));
      form.append("lng", String(coords.lng));
      form.append("description", description.trim());
      photos.forEach((photo) => {
        // Expo SDK 58: the global fetch IS expo/fetch, which only accepts real Blob/File
        // bodies. The old React Native hack `{ uri, name, type } as unknown as Blob` is
        // rejected before the request is even sent. expo-file-system's File is a proper
        // Blob that streams the photo from disk.
        form.append("photos", new File(photo.uri));
      });
      return reportsApi.create(form);
    },
    onSuccess: (report) => {
      // Lists that contain reports are now out of date.
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      setCategory(null);
      setPhotos([]);
      setDescription("");
      Alert.alert(
        "Murojaat yuborildi ✅",
        report.duplicate_of
          ? "Bu joyda shunday muammo allaqachon bildirilgan — murojaatingiz unga biriktirildi."
          : "Moderator tekshirgach, xaritada paydo bo'ladi va sizga +10 Eco Ball beriladi.",
      );
      router.push({ pathname: "/report/[id]", params: { id: report.id } });
    },
  });

  // A report must carry the REAL location of the problem: the Tashkent-centre fallback
  // that the air screen uses would put the report in the wrong place.
  const hasRealLocation = !!location.data && !location.data.isFallback;
  const canSubmit = !!category && photos.length > 0 && hasRealLocation;
  const errors = fieldErrors(create.error);
  const firstError = errors.photos ?? errors.lat ?? errors.category ?? errors.non_field_errors;

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
      {create.error ? (
        <ErrorBanner message={firstError ?? errorMessage(create.error)} />
      ) : null}

      <Text style={styles.section}>1. Muammo turi</Text>
      <View style={styles.categories}>
        {(categories.data ?? []).map((item) => {
          const selected = item.slug === category;
          return (
            <Pressable
              key={item.slug}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              onPress={() => setCategory(item.slug)}
              style={[styles.category, selected && styles.categorySelected]}
            >
              <Ionicons
                name={categoryIcon(item.slug)}
                size={20}
                color={selected ? "#fff" : colors.primary}
              />
              <Text style={[styles.categoryText, selected && { color: "#fff" }]}>
                {item.name_uz}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.section}>2. Rasmlar</Text>
      <PhotoPicker photos={photos} onChange={setPhotos} />

      <Text style={styles.section}>3. Joylashuv</Text>
      <View style={styles.location}>
        <Ionicons
          name={hasRealLocation ? "location" : "location-outline"}
          size={20}
          color={hasRealLocation ? colors.primary : colors.danger}
        />
        <Text style={{ flex: 1, color: colors.text }}>
          {hasRealLocation
            ? `${location.data!.lat.toFixed(5)}, ${location.data!.lng.toFixed(5)}`
            : "Aniq joylashuv kerak. Joylashuvga ruxsat bering."}
        </Text>
        <Pressable onPress={() => location.refetch()} accessibilityLabel="Joylashuvni yangilash">
          <Ionicons name="refresh" size={20} color={colors.primary} />
        </Pressable>
      </View>

      <Text style={styles.section}>4. Izoh (ixtiyoriy)</Text>
      <Field
        label=""
        value={description}
        onChangeText={setDescription}
        placeholder="Masalan: ariq bo'yida qurilish chiqindilari"
        multiline
        maxLength={500}
        style={{ minHeight: 90, textAlignVertical: "top" }}
      />

      <Button
        title="Yuborish"
        onPress={() => create.mutate()}
        disabled={!canSubmit}
        loading={create.isPending}
      />
      {!canSubmit ? (
        <Text style={styles.hint}>Turini tanlang, kamida bitta rasm qo'shing va joylashuvni aniqlang.</Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: spacing.md, paddingBottom: spacing.xl },
  section: { fontWeight: "700", fontSize: 16, color: colors.text, marginTop: spacing.md, marginBottom: spacing.sm },
  categories: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  category: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.lg,
    borderWidth: 1.5,
    borderColor: colors.primary,
    backgroundColor: colors.card,
  },
  categorySelected: { backgroundColor: colors.primary },
  categoryText: { color: colors.primary, fontWeight: "600" },
  location: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    backgroundColor: colors.card,
    borderRadius: radius.md,
    padding: spacing.md,
  },
  hint: { color: colors.muted, textAlign: "center", marginTop: spacing.sm, fontSize: 13 },
});
