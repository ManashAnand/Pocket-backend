import React, { useState } from "react";
import { View, Button, Text, TextInput, ScrollView } from "react-native";
import * as Linking from "expo-linking";

export default function FetchScreen() {
  const [email, setEmail] = useState("");
  const [authLink, setAuthLink] = useState<string | null>(null);
  const [rawResponse, setRawResponse] = useState<string | null>(null);
  const [emails, setEmails] = useState<any[]>([]);

  const fetchEmails = async () => {
    if (!email.trim()) {
      alert("Please enter your email first.");
      return;
    }

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
        setEmails([]);
        return;
      }

      if (data.emails) {
        setEmails(data.emails);
        setRawResponse(null);
        setAuthLink(null);
        return;
      }

      setRawResponse(JSON.stringify(data, null, 2));
    } catch (err) {
      console.log("FETCH ERROR:", err);
    }
  };

  const openAuthLink = () => {
    if (authLink) Linking.openURL(authLink);
  };

  return (
    <ScrollView
      style={{ marginTop: 60, padding: 20 }}
      contentContainerStyle={{ gap: 20 }}
    >
      <Text style={{ fontSize: 22, fontWeight: "bold" }}>
        Gmail Fetch (Multi-user)
      </Text>

      {/* Email Input */}
      <TextInput
        placeholder="Enter your email"
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

      {/* Button */}
      <Button title="Fetch Emails / Login" onPress={fetchEmails} />

      {/* OAuth Link Button */}
      {authLink && (
        <View style={{ marginTop: 10 }}>
          <Button title="Open Google Authorization" onPress={openAuthLink} />
        </View>
      )}

      {/* Show Emails */}
      {emails.length > 0 && (
        <View style={{ marginTop: 20 }}>
          <Text style={{ fontSize: 20, fontWeight: "bold" }}>
            Latest Emails:
          </Text>

          {emails.map((item, index) => (
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
              <Text style={{ fontWeight: "bold" }}>From:</Text>
              <Text>{item.from}</Text>

              <Text style={{ fontWeight: "bold", marginTop: 6 }}>Subject:</Text>
              <Text>{item.subject}</Text>

              <Text style={{ fontWeight: "bold", marginTop: 6 }}>Date:</Text>
              <Text>{item.date}</Text>

              <Text style={{ fontWeight: "bold", marginTop: 6 }}>Snippet:</Text>
              <Text>{item.snippet}</Text>
            </View>
          ))}
        </View>
      )}

      {/* Raw Response (Debug) */}
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
