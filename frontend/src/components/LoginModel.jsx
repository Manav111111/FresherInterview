import { useState } from "react";
import { signInWithPopup } from "firebase/auth";
import { auth, provider } from "../utils/firebase";
import { FcGoogle } from "react-icons/fc";
import { FiX, FiZap, FiCheckCircle } from "react-icons/fi";
import { GiArtificialHive } from "react-icons/gi";
import { loginWithFirebaseToken, demoLoginUser } from "../api/user.api";
import { useNavigate } from "react-router-dom";

export function LoginModal({ onClose, setUser }) {
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const navigate = useNavigate();

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      setErrorMsg("");
      const result = await signInWithPopup(auth, provider);
      const fbUser = result.user;
      const token = await fbUser.getIdToken();

      let candidateUser = {
        userId: fbUser.uid,
        _id: fbUser.uid,
        id: fbUser.uid,
        name: fbUser.displayName || "Fresher Candidate",
        email: fbUser.email || "candidate@fresherai.com",
        photoURL: fbUser.photoURL,
        interviewCoin: 150,
      };

      try {
        const response = await loginWithFirebaseToken(token);
        if (response?.user) {
          candidateUser = response.user;
        }
      } catch (apiErr) {
        console.warn("Backend auth sync notice (proceeding with verified Firebase identity):", apiErr);
      }

      localStorage.setItem("fresherai_token", token);
      localStorage.setItem("fresherai_demo_user", JSON.stringify(candidateUser));
      setUser(candidateUser);
      onClose();
      navigate("/dashboard");
    } catch (error) {
      console.error("Google authentication failed:", error);
      if (error.code === "auth/popup-closed-by-user") {
        setErrorMsg("Sign-in popup was closed. Please try again.");
      } else if (error.code === "auth/unauthorized-domain") {
        setErrorMsg("Domain authorization notice: Please add 'fresherai-silk.vercel.app' in Firebase Authorized Domains or use Instant Demo.");
      } else {
        setErrorMsg(error.message || "Google sign-in could not be completed. You can use Instant Demo below.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    try {
      setLoading(true);
      setErrorMsg("");
      const demoCandidate = {
        userId: "demo_candidate_uid",
        _id: "demo_candidate_uid",
        id: "demo_candidate_uid",
        name: "Fresher Candidate",
        email: "candidate@fresherai.com",
        interviewCoin: 150,
      };
      localStorage.setItem("fresherai_token", "demo_candidate_token");
      localStorage.setItem("fresherai_demo_user", JSON.stringify(demoCandidate));
      setUser(demoCandidate);
      onClose();
      navigate("/dashboard");

      // Non-blocking background sync with Render backend
      try {
        await demoLoginUser();
      } catch (syncErr) {
        console.warn("Backend demo sync:", syncErr?.message || syncErr);
      }
    } catch (error) {
      console.error("Demo login error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm px-4">
      <div className="relative w-full max-w-md bg-white border border-slate-200/80 rounded-3xl overflow-hidden shadow-2xl transition-all">
        {/* Header */}
        <div className="relative p-7 text-center">
          <button
            onClick={onClose}
            className="absolute top-5 right-5 text-slate-400 hover:text-slate-700 p-1.5 rounded-full hover:bg-slate-100 transition cursor-pointer"
          >
            <FiX size={18} />
          </button>

          {/* Logo Badge */}
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 mx-auto mb-3">
            <GiArtificialHive size={24} />
          </div>

          <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
            Sign in to <span className="text-[#4F46E5]">Fresher.AI</span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Accelerate your engineering career with AI mock interviews
          </p>

          {/* Error Message if any */}
          {errorMsg && (
            <div className="mt-3 p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs text-left leading-relaxed">
              ⚠️ {errorMsg}
            </div>
          )}

          {/* Action Buttons */}
          <div className="mt-6 space-y-3">
            {/* Google OAuth Button */}
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 py-3.5 rounded-2xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-bold text-xs sm:text-sm shadow-xs transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <FcGoogle size={20} />
              <span>{loading ? "Connecting..." : "Continue with Google"}</span>
            </button>

            {/* Instant Demo Access Button */}
            <button
              onClick={handleDemoLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold text-xs sm:text-sm shadow-md shadow-purple-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              <FiZap className="text-amber-300" size={16} />
              <span>Instant Demo / Local Test Access</span>
            </button>
          </div>
        </div>

        {/* Benefits Footnote */}
        <div className="border-t border-slate-100 bg-slate-50/70 px-6 py-3.5 flex items-center justify-between text-[11px] text-slate-500">
          <span className="flex items-center gap-1.5">
            <FiCheckCircle size={13} className="text-emerald-500" />
            150 Free Coins Included
          </span>
          <span>FastAPI &amp; Firebase Secured</span>
        </div>
      </div>
    </div>
  );
}
export default LoginModal;