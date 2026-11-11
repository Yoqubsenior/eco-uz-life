import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

import { AuthProvider } from "@/auth/AuthProvider";
import { colors } from "@/lib/theme";

// One cache for the whole app. Created at module level so it survives re-renders.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1, // one retry for flaky mobile networks, not an endless spinner
      staleTime: 60_000, // air data changes hourly; don't refetch on every screen focus
    },
  },
});

export default function RootLayout() {
  return (
    // QueryClientProvider must wrap AuthProvider: signing out clears the query cache.
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerTintColor: colors.primary,
            contentStyle: { backgroundColor: colors.background },
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="login" options={{ title: "Kirish", presentation: "modal" }} />
          <Stack.Screen
            name="register"
            options={{ title: "Ro'yxatdan o'tish", presentation: "modal" }}
          />
          <Stack.Screen name="report/[id]" options={{ title: "Murojaat" }} />
        </Stack>
      </AuthProvider>
    </QueryClientProvider>
  );
}
