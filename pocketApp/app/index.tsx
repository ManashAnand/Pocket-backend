import React, { useState } from "react";
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

export default function FetchScreen() {
  const [email, setEmail] = useState("");
  const [authLink, setAuthLink] = useState<string | null>(null);
  const [rawResponse, setRawResponse] = useState<string | null>(null);
  const [jobEmails, setJobEmails] = useState<JobEmail[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchEmails = async () => {
    if (!email.trim()) {
      alert("Please enter your email first.");
      return;
    }

    setLoading(true);
    setRawResponse(null);
    setJobEmails([]);
    setAuthLink(null);

    try {
      const res = await fetch(
        `https://pocket-backend-mjhf.onrender.com/emails/latest?user_email=${encodeURIComponent(
          email.trim()
        )}&limit=5`
      );

      const data = await res.json();
      console.log("API DATA:", data);

      if (data.auth_url) {
        setAuthLink(data.auth_url);
        setRawResponse(JSON.stringify(data, null, 2));
        return;
      }

      if (data.job_emails) {
        setJobEmails(data.job_emails);
        return;
      }

      setRawResponse(JSON.stringify(data, null, 2));
    } catch (err) {
      console.log("FETCH ERROR:", err);
      alert("Something went wrong. Check console.");
    } finally {
      setLoading(false);
    }
  };

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

      {/* Email Input */}
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

      {/* Fetch Button */}
      <Button
        title={loading ? "Fetching..." : "Fetch Emails / Login"}
        onPress={fetchEmails}
        disabled={loading}
      />

      {/* OAuth Button */}
      {authLink && (
        <View>
          <Button title="Open Google Authorization" onPress={openAuthLink} />
        </View>
      )}

      {/* Job Results */}
      {jobEmails.length > 0 && (
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

      {/* Debug Output */}
      {rawResponse && (
        <Text style={{ marginTop: 20, fontFamily: "monospace" }}>
          Raw Response:
          {"\n"}
          {rawResponse}
        </Text>
      )}
    </ScrollView>
  );
}
