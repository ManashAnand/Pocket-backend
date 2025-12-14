import React, { useState, useEffect, useRef } from "react";
import {
  View,
  Button,
  Text,
  TextInput,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import * as Linking from "expo-linking";
import BackendHealth from "../components/backendHealth";

type JobEmail = {
  company_name: string;
  date: string;
  verdict: string;
};

const BACKEND = "https://pocket-backend-mjhf.onrender.com";

/* ================= VERDICT CONFIG ================= */

const verdictMeta: Record<
  string,
  { label: string; color: string; priority: number }
> = {
  rejected: { label: "Rejected", color: "#e53935", priority: 1 },
  application_received: {
    label: "Applied",
    color: "#fbc02d",
    priority: 2,
  },
  referred: { label: "Referred", color: "#43a047", priority: 3 },
  oa_received: { label: "OA Received", color: "#43a047", priority: 3 },
  interview_scheduled: {
    label: "Interview",
    color: "#43a047",
    priority: 3,
  },
  offer_received: { label: "Offer", color: "#2e7d32", priority: 4 },
  unknown: { label: "Unknown", color: "#9e9e9e", priority: 0 },
};

const FILTERS = ["all", "positive", "applied", "rejected"] as const;
type FilterType = (typeof FILTERS)[number];

/* ================= COMPONENT ================= */

export default function FetchScreen() {
  const [email, setEmail] = useState("");
  const [authLink, setAuthLink] = useState<string | null>(null);
  const [jobEmails, setJobEmails] = useState<JobEmail[]>([]);
  const [status, setStatus] = useState<
    "idle" | "processing" | "done" | "error"
  >("idle");

  const [filter, setFilter] = useState<FilterType>("all");
  const [loading, setLoading] = useState(false);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  /* ================= START ================= */

  const startFetch = async () => {
    if (!email.trim()) {
      alert("Enter your email");
      return;
    }

    setLoading(true);
    setJobEmails([]);
    if (status === "processing") return;

    try {
      const res = await fetch(
        `${BACKEND}/emails/latest?user_email=${encodeURIComponent(
          email.trim()
        )}&limit=300`
      );

      const data = await res.json();

      if (data.auth_url) {
        setAuthLink(data.auth_url);
        setLoading(false);
        return;
      }

      if (data.status === "started" || data.status === "processing") {
        setStatus("processing");
        startPolling();
      }
    } catch {
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  /* ================= POLLING ================= */

  const pollStatus = async () => {
    const res = await fetch(
      `${BACKEND}/emails/status?user_email=${encodeURIComponent(email.trim())}`
    );
    const data = await res.json();

    if (data.status === "done") {
      stopPolling();
      setJobEmails(data.job_emails || []);
      setStatus("done");
    } else if (data.status === "error") {
      stopPolling();
      setStatus("error");
    }
  };

  const startPolling = () => {
    if (!pollingRef.current) {
      pollingRef.current = setInterval(pollStatus, 3000);
    }
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => () => stopPolling(), []);

  /* ================= FILTER + SORT ================= */

  const filtered = jobEmails
    .filter((e) => {
      if (filter === "all") return true;
      if (filter === "rejected") return e.verdict === "rejected";
      if (filter === "applied") return e.verdict === "application_received";
      if (filter === "positive")
        return [
          "oa_received",
          "interview_scheduled",
          "offer_received",
        ].includes(e.verdict);
      return true;
    })
    .sort((a, b) => {
      const pa = verdictMeta[a.verdict]?.priority ?? 0;
      const pb = verdictMeta[b.verdict]?.priority ?? 0;
      return pb - pa;
    });

  /* ================= UI ================= */

  return (
    <ScrollView style={{ marginTop: 60, padding: 20 }}>
      <Text style={{ fontSize: 22, fontWeight: "bold" }}>
        Gmail Job Tracker
      </Text>

      <BackendHealth backendUrl={BACKEND} />

      <TextInput
        placeholder="Enter Gmail"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        style={{
          marginTop: 12,
          padding: 12,
          borderWidth: 1,
          borderRadius: 8,
        }}
      />

      <Button
        title={loading ? "Fetching…" : "Fetch Emails"}
        onPress={startFetch}
        disabled={loading}
      />

      {authLink && (
        <Button
          title="Authorize Gmail"
          onPress={() => Linking.openURL(authLink)}
        />
      )}

      {status === "processing" && (
        <Text style={{ marginTop: 12 }}>Processing…</Text>
      )}

      {status === "error" && (
        <Text style={{ color: "red" }}>Something went wrong</Text>
      )}

      {/* FILTER BAR */}
      {status === "done" && (
        <View style={{ flexDirection: "row", marginTop: 16 }}>
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f}
              onPress={() => setFilter(f)}
              style={{
                marginRight: 8,
                paddingVertical: 6,
                paddingHorizontal: 12,
                borderRadius: 20,
                backgroundColor: filter === f ? "#333" : "#ddd",
              }}
            >
              <Text style={{ color: filter === f ? "#fff" : "#000" }}>
                {f.toUpperCase()}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* RESULTS */}
      {filtered.map((item, i) => {
        const meta = verdictMeta[item.verdict] || verdictMeta.unknown;

        return (
          <View
            key={i}
            style={{
              marginTop: 12,
              padding: 12,
              borderWidth: 1,
              borderRadius: 8,
            }}
          >
            <Text style={{ fontWeight: "bold" }}>
              {item.company_name || "Unknown"}
            </Text>

            <Text style={{ color: "#555", marginTop: 4 }}>{item.date}</Text>

            {/* STATUS BADGE */}
            <View
              style={{
                marginTop: 8,
                alignSelf: "flex-start",
                paddingVertical: 4,
                paddingHorizontal: 10,
                borderRadius: 14,
                backgroundColor: meta.color,
              }}
            >
              <Text style={{ color: "#fff", fontWeight: "bold" }}>
                {meta.label}
              </Text>
            </View>
          </View>
        );
      })}
    </ScrollView>
  );
}
