import Ionicons from "@expo/vector-icons/Ionicons";
import * as ImagePicker from "expo-image-picker";
import { Alert, Image, Pressable, StyleSheet, Text, View } from "react-native";

import { colors, radius, spacing } from "@/lib/theme";

export const MAX_PHOTOS = 3;
const MAX_BYTES = 5 * 1024 * 1024; // same limit as the server — fail fast, before uploading

export type PickedPhoto = { uri: string; mimeType: string; fileName: string };

const PICKER_OPTIONS: ImagePicker.ImagePickerOptions = {
  mediaTypes: ["images"], // SDK 58: array of media types (MediaTypeOptions is deprecated)
  quality: 0.7, // smaller upload on mobile data; the server re-encodes anyway
  exif: false, // we don't need EXIF in JS. Note: this does NOT strip it from the file —
  // the server removes all metadata (GPS included) when it re-encodes the photo.
};

function toPhoto(asset: ImagePicker.ImagePickerAsset): PickedPhoto | null {
  if (asset.fileSize && asset.fileSize > MAX_BYTES) return null;
  return {
    uri: asset.uri,
    mimeType: asset.mimeType ?? "image/jpeg",
    fileName: asset.fileName ?? `photo-${Date.now()}.jpg`,
  };
}

type Props = { photos: PickedPhoto[]; onChange: (photos: PickedPhoto[]) => void };

export function PhotoPicker({ photos, onChange }: Props) {
  const remaining = MAX_PHOTOS - photos.length;

  const add = (assets: ImagePicker.ImagePickerAsset[]) => {
    const accepted = assets.map(toPhoto).filter((p): p is PickedPhoto => p !== null);
    if (accepted.length < assets.length) {
      Alert.alert("Rasm juda katta", "5 MB dan katta rasmlar qo'shilmadi.");
    }
    onChange([...photos, ...accepted].slice(0, MAX_PHOTOS));
  };

  const takePhoto = async () => {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert("Kameraga ruxsat yo'q", "Sozlamalardan kameraga ruxsat bering.");
      return;
    }
    const result = await ImagePicker.launchCameraAsync(PICKER_OPTIONS);
    if (!result.canceled) add(result.assets);
  };

  const pickFromGallery = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      ...PICKER_OPTIONS,
      allowsMultipleSelection: true,
      selectionLimit: remaining,
    });
    if (!result.canceled) add(result.assets);
  };

  return (
    <View>
      <View style={styles.row}>
        {photos.map((photo, index) => (
          <View key={photo.uri} style={styles.thumbWrap}>
            <Image source={{ uri: photo.uri }} style={styles.thumb} />
            <Pressable
              accessibilityLabel="Rasmni olib tashlash"
              style={styles.remove}
              onPress={() => onChange(photos.filter((_, i) => i !== index))}
            >
              <Ionicons name="close" size={16} color="#fff" />
            </Pressable>
          </View>
        ))}
      </View>

      {remaining > 0 ? (
        <View style={styles.row}>
          <Pressable style={styles.action} onPress={takePhoto}>
            <Ionicons name="camera-outline" size={22} color={colors.primary} />
            <Text style={styles.actionText}>Suratga olish</Text>
          </Pressable>
          <Pressable style={styles.action} onPress={pickFromGallery}>
            <Ionicons name="images-outline" size={22} color={colors.primary} />
            <Text style={styles.actionText}>Galereya</Text>
          </Pressable>
        </View>
      ) : null}
      <Text style={styles.hint}>
        {photos.length}/{MAX_PHOTOS} rasm · kamida bittasi majburiy
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.sm },
  thumbWrap: { position: "relative" },
  thumb: { width: 96, height: 96, borderRadius: radius.sm, backgroundColor: colors.border },
  remove: {
    position: "absolute",
    top: 4,
    right: 4,
    backgroundColor: "rgba(0,0,0,0.6)",
    borderRadius: 12,
    padding: 2,
  },
  action: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    borderWidth: 1.5,
    borderStyle: "dashed",
    borderColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
  },
  actionText: { color: colors.primary, fontWeight: "600" },
  hint: { color: colors.muted, fontSize: 13 },
});
