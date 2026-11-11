import { ApiError, NetworkError } from "@/api/client";

export type FieldErrors = Record<string, string>;

/** DRF validation body {"email": ["msg", ...]} -> {"email": "msg"} for showing under inputs. */
export function fieldErrors(error: unknown): FieldErrors {
  if (!(error instanceof ApiError) || error.status !== 400 || typeof error.body !== "object") {
    return {};
  }
  const result: FieldErrors = {};
  Object.entries(error.body as Record<string, unknown>).forEach(([field, value]) => {
    result[field] = Array.isArray(value) ? String(value[0]) : String(value);
  });
  return result;
}

/** One human-readable sentence for a banner. */
export function errorMessage(error: unknown): string {
  if (error instanceof NetworkError) {
    return "Serverga ulanib bo'lmadi. Internet yoki Wi-Fi ni tekshiring.";
  }
  if (error instanceof ApiError) {
    if (error.status === 401) return "Email yoki parol noto'g'ri.";
    if (error.status === 429) return "Juda ko'p urinish. Bir daqiqadan keyin qayta urining.";
    if (error.status >= 500) return "Serverda xatolik. Keyinroq urinib ko'ring.";
    const detail = (error.body as { detail?: string } | null)?.detail;
    if (detail) return detail;
  }
  return "Kutilmagan xatolik yuz berdi.";
}
