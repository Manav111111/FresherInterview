import { useState } from "react";
import { signInWithPopup } from "firebase/auth";
import { auth, provider } from "../utils/firebase";
import { FcGoogle } from "react-icons/fc";
import { FiX, FiZap } from "react-icons/fi";
import { loginWithFirebaseToken } from "../api/user.api";

export function LoginModal({ onClose, setUser }) {
  const [loading, setLoading] = useState(false);

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      const result = await signInWithPopup(auth, provider);
      const token = await result.user.getIdToken();
      const response = await loginWithFirebaseToken(token);
      if (response?.user) {
        setUser(response.user);
      }
      onClose();
    } catch (error) {
      console.error("Google authentication failed:", error);
      if (error.code !== "auth/popup-closed-by-user") {
        alert(error.message || "Google sign-in failed. Please ensure your domain is authorized in Firebase Console.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    try {
      setLoading(true);
      const response = await loginWithFirebaseToken("demo-candidate-token");
      if (response?.user) {
        setUser(response.user);
      }
      onClose();
    } catch (error) {
      console.error("Demo login error:", error);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="
      fixed inset-0 z-50
      flex items-center justify-center
      bg-black/40 backdrop-blur-md
      px-4
    ">
      <div className="
        relative w-full max-w-sm
        bg-[#0A0A0A]/80 backdrop-blur-2xl
        border border-white/10
        rounded-2xl
        overflow-hidden
        shadow-[0_8px_32px_rgba(0,0,0,0.25)]
      ">
        {/* glass sheen */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/[0.08] via-transparent to-transparent pointer-events-none" />

        {/* Header */}
        <div className="relative p-7">
          <button
            onClick={onClose}
            className="
              absolute top-4 right-4
              text-white/30 hover:text-white
              transition-colors
            "
          >
            <FiX size={16} />
          </button>

          <h2 className="
            text-lg
            font-bold
            text-center
            mb-2
            text-white
          ">
            Sign in to{" "}
            <span className="font-extrabold text-lg tracking-tight text-white">
              Fresher.AI
            </span>
          </h2>

          <p className="
            text-white/45
            text-center
            text-xs
          ">
            Accelerate your career with AI mock interviews
          </p>

          {/* Action Buttons */}
          <div className="mt-6 space-y-3">
            {/* Google OAuth */}
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="
                w-full
                flex items-center justify-center gap-3
                py-3
                rounded-xl
                border border-white/15
                bg-white/10 backdrop-blur-md
                hover:border-white/25
                hover:bg-white/[0.14]
                shadow-inner
                transition-all
                disabled:opacity-50 disabled:cursor-not-allowed
              "
            >
              <FcGoogle size={18} />
              <span className="text-white font-medium text-sm">
                {loading ? "Signing in..." : "Continue with Google"}
              </span>
            </button>

            {/* Instant Demo Access Button */}
            <button
              onClick={handleDemoLogin}
              disabled={loading}
              className="
                w-full
                flex items-center justify-center gap-2
                py-2.5
                rounded-xl
                border border-purple-500/30
                bg-purple-600/20 backdrop-blur-md
                hover:bg-purple-600/30 hover:border-purple-500/50
                shadow-inner
                transition-all
                disabled:opacity-50 disabled:cursor-not-allowed
              "
            >
              <FiZap className="text-purple-400" size={15} />
              <span className="text-purple-200 font-medium text-xs">
                Instant Demo / Local Test Access
              </span>
            </button>

          </div>
        </div>

        {/* Bottom */}
        <div className="
          relative
          border-t border-white/10
          bg-black/30
          p-4
          text-center
        ">
          <p className="text-white/30 text-xs">
            Powered by Firebase Auth & FastAPI
          </p>
        </div>
      </div>
    </div>
  );
}