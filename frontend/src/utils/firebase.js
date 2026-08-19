
import { initializeApp, getApps } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_APIKEY || "AIzaSyB6XxJcuQBbtyYJz8Tv2p3G18c2cfYgctI",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "interview-4d457.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "interview-4d457",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "interview-4d457.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "23413833230",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:23413833230:web:e30947b5cd74e332a0865f",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || "G-6WQSRRSQPN",
};

// Initialize Firebase safely (avoid multi-init in HMR)
const app = !getApps().length ? initializeApp(firebaseConfig) : getApps()[0];

const auth = getAuth(app);
const provider = new GoogleAuthProvider();
provider.setCustomParameters({ prompt: "select_account" });

export { auth, provider, app };
