import type { Tokens } from "@/lib/tokens";

import { api } from "./client";
import type { NearestStation, PointsSummary, User } from "./types";

export const authApi = {
  login: (email: string, password: string) =>
    api<Tokens>("/auth/login/", { method: "POST", body: { email, password }, auth: false }),

  register: (data: { email: string; password: string; display_name?: string }) =>
    api<User>("/auth/register/", { method: "POST", body: data, auth: false }),

  logout: (refresh: string) =>
    api<null>("/auth/logout/", { method: "POST", body: { refresh }, auth: false }),

  me: () => api<User>("/auth/me/"),
};

export const airApi = {
  nearest: (lat: number, lng: number) =>
    api<NearestStation>("/air/nearest/", { query: { lat, lng }, auth: false }),
};

export const pointsApi = {
  mine: () => api<PointsSummary>("/points/me/"),
};
