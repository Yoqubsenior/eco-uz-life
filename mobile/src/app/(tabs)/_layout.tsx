import Ionicons from "@expo/vector-icons/Ionicons";
import { Tabs } from "expo-router";

import { colors } from "@/lib/theme";

type IconName = keyof typeof Ionicons.glyphMap;

// We pick the icon colour ourselves from `focused` instead of using the `color` argument:
// its type (ColorValue) also allows null/number, which Ionicons doesn't accept.
// Same colours as the tab labels, so icons and text always match.
function tabIcon(name: IconName) {
  return function TabIcon({ focused, size }: { focused: boolean; size: number }) {
    return <Ionicons name={name} size={size} color={focused ? colors.primary : colors.muted} />;
  };
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        headerTitleStyle: { fontWeight: "700" },
        sceneStyle: { backgroundColor: colors.background },
      }}
    >
      <Tabs.Screen name="index" options={{ title: "Havo", tabBarIcon: tabIcon("cloud-outline") }} />
      <Tabs.Screen
        name="profile"
        options={{ title: "Profil", tabBarIcon: tabIcon("person-outline") }}
      />
    </Tabs>
  );
}
