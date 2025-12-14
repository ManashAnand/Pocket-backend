import React, { useState, useEffect, useRef } from "react";
import { View, Button, Text, TextInput, ScrollView } from "react-native";
import * as Linking from "expo-linking";

type JobEmail = {
  company_name: string;
  date: string;
  verdict: string;
};

const verdictLabel: Record<string, string> = {
  oa_received: "OA Received",
  rejected: "Rejected",
  ghosted: "Ghosted",
  referred_no_response: "Referred (No Response)",
  interview_scheduled: "Interview Scheduled",
  application_received: "Application Submitted",
  unknown: "Unknown",
};

const BACKEND = "https://pocket-backend-mjhf.onrender.com";

export default function FetchScreen() {
  const [email, setEmail] = useState("");
  const [authLink, setAuthLink] = useState<string | null>(null);
  const [jobEmails, setJobEmails] = useState<JobEmail[]>([]);
  const [status, setStatus] = useState<
    "idle" | "started" | "processing" | "done" | "error"
  >("idle");
  const [loading, setLoading] = useState(false);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  /* ---------------- START JOB ---------------- */

  const startFetch = async () => {
    if (!email.trim()) {
      alert("Please enter your email first.");
      return;
    }

    setLoading(true);
    setAuthLink(null);
    setJobEmails([]);
    setStatus("idle");

    try {
      const res = await fetch(
        `${BACKEND}/emails/latest?user_email=${encodeURIComponent(
          email.trim()
        )}&limit=150`
      );

      const data = await res.json();
      console.log("START RESPONSE:", data);

      if (data.auth_url) {
        setAuthLink(data.auth_url);
        setLoading(false);
        return;
      }

      if (data.status === "started" || data.status === "processing") {
        setStatus("processing");
        startPolling();
        return;
      }
    } catch (err) {
      console.log("START ERROR:", err);
      alert("Failed to start processing");
      setStatus("error");
    } finally {
      setLoading(false);
    }
  };

  /* ---------------- POLLING ---------------- */

  const pollStatus = async () => {
    try {
      const res = await fetch(
        `${BACKEND}/emails/status?user_email=${encodeURIComponent(
          email.trim()
        )}`
      );
      const data = await res.json();
      console.log("POLL RESPONSE:", data);

      if (data.status === "done") {
        setJobEmails(data.job_emails || []);
        setStatus("done");
        stopPolling();
      } else if (data.status === "error") {
        setStatus("error");
        stopPolling();
      } else {
        setStatus("processing");
      }
    } catch (err) {
      console.log("POLL ERROR:", err);
    }
  };

  const startPolling = () => {
    if (pollingRef.current) return;

    pollingRef.current = setInterval(pollStatus, 3000); // every 3s
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling(); // cleanup on unmount
  }, []);

  /* ---------------- UI ---------------- */

  const openAuthLink = () => {
    if (authLink) {
      Linking.openURL(authLink);
    }
  };

  return (
    <ScrollView
      style={{ marginTop: 60, padding: 20 }}
      contentContainerStyle={{ gap: 20 }}
    >
      <Text style={{ fontSize: 22, fontWeight: "bold" }}>
        Gmail Job Tracker
      </Text>

      <TextInput
        placeholder="Enter your Gmail"
        value={email}
        onChangeText={setEmail}
        autoCapitalize="none"
        keyboardType="email-address"
        style={{
          padding: 12,
          borderWidth: 1,
          borderRadius: 8,
          borderColor: "#999",
          fontSize: 16,
        }}
      />

      <Button
        title={loading ? "Starting..." : "Fetch Emails / Login"}
        onPress={startFetch}
        disabled={loading}
      />

      {authLink && (
        <Button title="Open Google Authorization" onPress={openAuthLink} />
      )}

      {status === "processing" && (
        <Text style={{ fontSize: 16 }}>Processing emails… please wait ⏳</Text>
      )}

      {status === "error" && (
        <Text style={{ color: "red" }}>Something went wrong. Try again.</Text>
      )}

      {status === "done" && jobEmails.length > 0 && (
        <View style={{ marginTop: 10 }}>
          <Text style={{ fontSize: 20, fontWeight: "bold" }}>
            Job Application Status
          </Text>

          {jobEmails.map((item, index) => (
            <View
              key={index}
              style={{
                marginTop: 10,
                padding: 12,
                borderWidth: 1,
                borderRadius: 8,
                borderColor: "#ccc",
              }}
            >
              <Text style={{ fontWeight: "bold" }}>Company</Text>
              <Text>{item.company_name || "Unknown"}</Text>

              <Text style={{ fontWeight: "bold", marginTop: 6 }}>Date</Text>
              <Text>{item.date || "Not found"}</Text>

              <Text style={{ fontWeight: "bold", marginTop: 6 }}>Verdict</Text>
              <Text>{verdictLabel[item.verdict] || item.verdict}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}
