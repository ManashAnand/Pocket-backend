import React, { useState } from "react";
import { View, Button, Text } from "react-native";
import * as Linking from "expo-linking";

export default function FetchScreen() {
  const [authLink, setAuthLink] = useState<string | null>(null);
  const [rawResponse, setRawResponse] = useState<string | null>(null);

  const fetchEmails = async () => {
    try {
      const res = await fetch(
        // "http://192.168.0.4:8000/emails/latest?limit=5"
        "https://pocket-backend-mjhf.onrender.com/emails/latest?limit=5"
      );

      const data = await res.json(); // <-- IMPORTANT

      console.log("API DATA:", data);

      if (data.auth_url) {
        setAuthLink(data.auth_url);
        setRawResponse(JSON.stringify(data, null, 2));
        return;
      }

      if (data.emails) {
        setRawResponse(JSON.stringify(data, null, 2));
        return;
      }
    } catch (err) {
      console.log("FETCH ERROR:", err);
    }
  };

  const openAuthLink = () => {
    if (authLink) {
      Linking.openURL(authLink);
    }
  };

  return (
    <View style={{ marginTop: 80, padding: 20, gap: 20 }}>
      {/* Fetch button */}
      <Button title="Fetch Emails / Generate OAuth URL" onPress={fetchEmails} />

      {/* Raw text response */}
      {rawResponse && (
        <Text style={{ marginTop: 20 }}>
          Raw Response:{"\n"} {rawResponse}
        </Text>
      )}

      {/* OAuth link button */}
      {authLink && (
        <Button title="Open Google Authorization" onPress={openAuthLink} />
      )}

      {/* Show extracted link */}
      {authLink && (
        <Text style={{ marginTop: 20 }}>
          OAuth URL:{"\n"} {authLink}
        </Text>
      )}
    </View>
  );
}
