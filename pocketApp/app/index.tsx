import React, { useState, useEffect, useRef } from "react";
import { View, Button, Text, TextInput, ScrollView } from "react-native";
import * as Linking from "expo-linking";
import BackendHealth from "../components/backendHealth";

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
  offer_received: "Offer Received",
  unknown: "Unknown",
};

const BACKEND = "https://pocket-backend-mjhf.onrender.com";

export default function FetchScreen() {
  const [email, setEmail] = useState("");
  const [authLink, setAuthLink] = useState<string | null>(null);
  const [jobEmails, setJobEmails] = useState<JobEmail[]>([]);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState(false);

  const [status, setStatus] = useState<
    "idle" | "processing" | "done" | "error"
  >("idle");

  const [loading, setLoading] = useState(false);

  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  /* ================= START JOB ================= */

  const startFetch = async () => {
    if (!email.trim()) {
      alert("Please enter your email first.");
      return;
    }

    setLoading(true);
    setAuthLink(null);
    setJobEmails([]);
    setInfoMessage(null);

    try {
      const res = await fetch(
        `${BACKEND}/emails/latest?user_email=${encodeURIComponent(
          email.trim()
        )}&limit=300`
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

  /* ================= POLLING ================= */

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
        stopPolling();
        setStatus("done");

        // EMPTY BUT VALID RESULT
        if (data.job_emails?.message) {
          setInfoMessage(data.job_emails.message);
          setJobEmails([]);
        } else {
          setInfoMessage(null);
          setJobEmails(data.job_emails || []);
        }
      } else if (data.status === "error") {
        stopPolling();
        setStatus("error");
      } else {
        setStatus("processing");
      }
    } catch (err) {
      console.log("POLL ERROR:", err);
    }
  };

  const startPolling = () => {
    if (pollingRef.current) return;
    pollingRef.current = setInterval(pollStatus, 3000);
  };

  const stopPolling = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  /* ================= UI ================= */

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

      <BackendHealth
        backendUrl="https://pocket-backend-mjhf.onrender.com"
        onOnline={() => console.log("Backend is ready")}
      />

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
        title={
          !backendOnline
            ? "Backend starting…"
            : loading
            ? "Fetching…"
            : "Fetch Emails / Login"
        }
        onPress={startFetch}
        disabled={!backendOnline || loading}
      />

      {authLink && (
        <Button title="Open Google Authorization" onPress={openAuthLink} />
      )}

      {status === "processing" && (
        <Text style={{ fontSize: 16 }}>Processing emails… please wait</Text>
      )}

      {status === "error" && (
        <Text style={{ color: "red" }}>Something went wrong. Try again.</Text>
      )}

      {/* EMPTY BUT VALID RESULT */}
      {status === "done" && infoMessage && (
        <Text style={{ marginTop: 12, color: "#666" }}>{infoMessage}</Text>
      )}

      {/* RESULTS */}
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
