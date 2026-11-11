import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { onSessionExpired } from "@/api/client";
import { authApi } from "@/api/endpoints";
import type { User } from "@/api/types";
import { clearTokens, getRefreshToken, saveTokens } from "@/lib/tokens";

type AuthStatus = "loading" | "signedIn" | "signedOut";

type AuthContextValue = {
  status: AuthStatus;
  user: User | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (data: { email: string; password: string; display_name?: string }) => Promise<void>;
  signOut: () => Promise<void>;
  setUser: (user: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);

  const resetSession = useCallback(() => {
    setUser(null);
    setStatus("signedOut");
    queryClient.clear(); // never show the previous user's cached data to the next one
  }, [queryClient]);

  // On app start: restore the session if a refresh token is stored.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!(await getRefreshToken())) {
        if (!cancelled) setStatus("signedOut");
        return;
      }
      try {
        const me = await authApi.me(); // the client refreshes the access token if needed
        if (!cancelled) {
          setUser(me);
          setStatus("signedIn");
        }
      } catch {
        if (!cancelled) setStatus("signedOut");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => onSessionExpired(resetSession), [resetSession]);

  const signIn = useCallback(async (email: string, password: string) => {
    const tokens = await authApi.login(email.trim(), password);
    await saveTokens(tokens);
    setUser(await authApi.me());
    setStatus("signedIn");
  }, []);

  const signUp = useCallback<AuthContextValue["signUp"]>(
    async (data) => {
      await authApi.register(data);
      await signIn(data.email, data.password);
    },
    [signIn],
  );

  const signOut = useCallback(async () => {
    const refresh = await getRefreshToken();
    if (refresh) {
      // Best effort: blacklist the token on the server. Even if offline, we log out locally.
      await authApi.logout(refresh).catch(() => undefined);
    }
    await clearTokens();
    resetSession();
  }, [resetSession]);

  return (
    <AuthContext.Provider value={{ status, user, signIn, signUp, signOut, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
