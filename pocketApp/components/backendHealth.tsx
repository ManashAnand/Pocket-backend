import React, { useEffect, useState } from "react";
import { View, Text, ActivityIndicator, TouchableOpacity } from "react-native";

type BackendStatus = "checking" | "online" | "offline";

type Props = {
  backendUrl: string;
  onOnline?: () => void;
};

export default function BackendHealth({ backendUrl, onOnline }: Props) {
  const [status, setStatus] = useState<BackendStatus>("checking");
  const [attempt, setAttempt] = useState(0);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${backendUrl}/nice-health`);
      if (res.ok) {
        setStatus("online");
        onOnline?.();
        return;
      }
      setStatus("offline");
    } catch {
      setStatus("offline");
    }
  };

  // Initial check
  useEffect(() => {
    checkHealth();
  }, []);

  // Retry when offline (Render cold start)
  useEffect(() => {
    if (status === "offline") {
      const timer = setTimeout(() => {
        setAttempt((a) => a + 1);
        checkHealth();
      }, 4000); // retry every 4s

      return () => clearTimeout(timer);
    }
  }, [status, attempt]);

  const bg =
    status === "online"
      ? "#e6fffa"
      : status === "offline"
      ? "#fff3cd"
      : "#eef2ff";

  const border =
    status === "online"
      ? "#2dd4bf"
      : status === "offline"
      ? "#facc15"
      : "#6366f1";

  return (
    <View
      style={{
        padding: 12,
        borderRadius: 10,
        borderWidth: 1,
        borderColor: border,
        backgroundColor: bg,
        flexDirection: "row",
        alignItems: "center",
        gap: 10,
      }}
    >
      {status !== "online" && <ActivityIndicator size="small" />}

      <View style={{ flex: 1 }}>
        <Text style={{ fontWeight: "600" }}>
          {status === "checking" && "Checking backend status…"}
          {status === "offline" && "Waking up backend…"}
          {status === "online" && "Backend online"}
        </Text>

        {status === "offline" && (
          <Text style={{ fontSize: 12, opacity: 0.7 }}>
            First request may take a few seconds (cold start)
          </Text>
        )}
      </View>

      {status === "offline" && (
        <TouchableOpacity onPress={checkHealth}>
          <Text style={{ color: "#2563eb", fontWeight: "600" }}>Retry</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
