import React, { useState } from "react";
import { View, Button, Text } from "react-native";

export default function FetchScreen() {
  const [data, setData] = useState(null);

  const fetchEmails = async () => {
    try {
      const res = await fetch("http://192.168.0.4:8000/emails/latest?limit=5");

      const json = await res.json();
      console.log("API RESPONSE:", json);
      setData(json);
    } catch (err) {
      console.log("FETCH ERROR:", err);
    }
  };

  return (
    <View style={{ marginTop: 80, padding: 20 }}>
      <Button title="Fetch Emails" onPress={fetchEmails} />

      {data && (
        <Text style={{ marginTop: 20 }}>{JSON.stringify(data, null, 2)}</Text>
      )}
    </View>
  );
}
