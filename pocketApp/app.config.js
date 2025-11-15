export default {
  expo: {
    name: "pocket",
    slug: "pocket",
    scheme: "pocket",

    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/images/icon.png",

    userInterfaceStyle: "automatic",
    newArchEnabled: true,

    ios: {
      supportsTablet: true,
    },

    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/images/android-icon-foreground.png",
        backgroundImage: "./assets/images/android-icon-background.png",
      },
    },

    web: {
      favicon: "./assets/images/favicon.png",
    },

    plugins: ["expo-router", "expo-web-browser"],
  },
};
