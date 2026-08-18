import { useNavigate } from "react-router-dom";
import { BsStars } from "react-icons/bs";
import PricingCard from "../components/PricingCard";
import { FiMenu, FiX } from "react-icons/fi";
import { useState } from "react";
import { createPaymentOrder, verifyPayment } from "../api/billing.api";
import { addCoins } from "../api/user.api";

function Coin() {
  return <BsStars className="text-yellow-400" size={14} />;
}

const plans = [
  {
    title: "Free",
    price: "Free",
    coins: 150,
    button: "Claimed Coins",
    popular: false,
    disabled: true,
    features: [
      "150 Initial Free Coins",
      "Interactive Resume Builder",
      "AI Resume Scorer",
      "AI Career Roadmap Generator",
    ],
  },
  {
    title: "Starter",
    price: "199",
    coins: 300,
    button: "Buy Now",
    popular: false,
    disabled: false,
    features: [
      "300 Interview Coins",
      "6 Full AI Mock Interviews",
      "Unlimited Resume ATS Scores",
      "Unlimited Career Roadmaps",
      "Priority Groq AI Processing",
    ],
  },
  {
    title: "Pro",
    price: "499",
    coins: 1000,
    button: "Buy Now",
    popular: true,
    disabled: false,
    features: [
      "1,000 Interview Coins",
      "20 Full AI Mock Interviews",
      "Voice & Webcam Analysis",
      "Unlimited Career Roadmaps",
      "Priority Candidate Evaluation",
    ],
  },
];

export default function Pricing({ user, setUser }) {
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);
  const [loadingPlan, setLoadingPlan] = useState("");

  const handlePayment = async (plan) => {
    if (plan.disabled) return;

    try {
      setLoadingPlan(plan.title);
      const result = await createPaymentOrder({
        planId: plan.title.toLowerCase(),
      });

      if (!result?.order) {
        throw new Error("Failed to initialize payment order");
      }

      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY_ID || "rzp_test_placeholder",
        amount: result.order.amount,
        currency: result.order.currency || "INR",
        name: "Fresher.AI",
        description: `${plan.title} - ${plan.coins} Interview Coins`,
        order_id: result.order.id,
        handler: async function (response) {
          try {
            // Verify Payment Signature
            await verifyPayment({
              razorpay_order_id: response.razorpay_order_id || result.order.id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature: response.razorpay_signature || "dev_signature",
            });

            // Add Coins
            const coinRes = await addCoins({
              coins: plan.coins,
            });

            // Update User State
            if (coinRes?.interviewCoin !== undefined) {
              setUser((prev) => ({
                ...prev,
                interviewCoin: coinRes.interviewCoin,
              }));
            }

            alert("Payment Successful 🎉 Coins have been credited to your account!");
            navigate("/dashboard");
          } catch (error) {
            console.error("Payment verification failed:", error);
            alert(
              error?.response?.data?.detail ||
              error?.response?.data?.message ||
              "Payment verification failed"
            );
          }
        },
        prefill: {
          name: user?.name || "",
          email: user?.email || "",
        },
        theme: {
          color: "#000000",
        },
      };

      if (window.Razorpay) {
        const razorpay = new window.Razorpay(options);
        razorpay.open();
      } else {
        // Fallback for dev mode if script blocked
        alert("Razorpay checkout is ready. In dev mode without live keys, simulating successful top-up.");
        options.handler({
          razorpay_order_id: result.order.id,
          razorpay_payment_id: `pay_${Date.now()}`,
          razorpay_signature: "mock_sig",
        });
      }
    } catch (err) {
      console.error("Payment initiation failed:", err);
      alert(err.response?.data?.detail || err.response?.data?.message || "Failed to start payment");
    } finally {
      setLoadingPlan("");
    }
  };



    return (
        <div className="min-h-screen bg-white text-[#0A0A0A]">

            {/* Navbar */}
            <nav className="sticky top-0 z-20 border-b border-black/8 bg-white/80 backdrop-blur-xl">
                <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-3 sm:px-5">

                    <div
                        onClick={() => navigate("/dashboard")}
                        className="flex cursor-pointer items-center gap-1.5"
                    >
                        <span className="text-base font-extrabold tracking-tight text-[#0A0A0A]">
                            Fresher.AI
                        </span>

                        <span className="hidden rounded bg-black/5 px-1.5 py-0.5 text-[10px] text-black/50 sm:block">
                            Interview Coins
                        </span>
                    </div>

                    <div className="relative">

                        <button
                            onClick={() => setShowMenu(!showMenu)}
                            className="flex h-8 w-8 items-center justify-center rounded-lg border border-black/15 text-black/60 transition hover:border-black/35 hover:text-[#0A0A0A]"
                        >
                            {showMenu ? <FiX size={16} /> : <FiMenu size={16} />}
                        </button>

                        {showMenu && (
                            <>
                                {/* Mobile Backdrop */}
                                <div
                                    onClick={() => setShowMenu(false)}
                                    className="fixed inset-0 z-30 bg-black/20 lg:hidden"
                                />

                                {/* Popup — black glass */}
                                <div className="absolute right-0 top-10 z-40 w-[240px] max-w-[calc(100vw-24px)] rounded-xl overflow-hidden bg-[#000000]/90 backdrop-blur-2xl border border-white/10 p-3.5 shadow-[0_8px_32px_rgba(0,0,0,0.25)]">

                                    {/* glass sheen */}
                                    <div className="absolute inset-0 bg-gradient-to-br from-white/[0.08] via-transparent to-transparent pointer-events-none" />

                                    {/* Coins */}
                                    <div className="relative flex items-center gap-2 border-b border-white/10 pb-3">
                                        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-yellow-500/15 border border-yellow-400/20">
                                            <BsStars className="text-yellow-400 text-sm" />
                                        </div>
                                        <div>
                                            <p className="text-[10px] text-white/40">
                                                Available Coins
                                            </p>
                                            <h2 className="text-lg font-bold text-white">
                                                {user?.interviewCoin}
                                            </h2>
                                        </div>
                                    </div>

                                    {/* Coin Usage */}
                                    <div className="relative mt-3.5 space-y-1.5">
                                        {[
                                            { title: "Resume Builder", coin: "-10" },
                                            { title: "Resume Scorer", coin: "-10" },
                                            { title: "Roadmap Generator", coin: "-20" },
                                            { title: "AI Interview", coin: "-50" },
                                        ].map((item) => (
                                            <div
                                                key={item.title}
                                                className="flex items-center justify-between rounded-lg bg-white/5 border border-white/8 px-2.5 py-1.5"
                                            >
                                                <span className="text-xs text-white/70">
                                                    {item.title}
                                                </span>
                                                <span className="text-xs font-bold text-red-400">
                                                    {item.coin}
                                                </span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Bottom Info */}
                                    <div className="relative mt-3.5 rounded-lg border border-violet-400/20 bg-violet-500/10 p-2.5">
                                        <p className="text-[10px] leading-4 text-violet-300">
                                            Every AI feature uses Interview Coins.
                                            Buy more coins anytime to continue using
                                            Resume Builder, Resume Scorer,
                                            AI Interview and Roadmap Generator.
                                        </p>
                                    </div>

                                </div>
                            </>
                        )}

                    </div>

                </div>
            </nav>

            <div className="mx-auto max-w-4xl px-4 py-6">

                <div className="text-center">
                    <h1 className="text-3xl font-bold text-[#0A0A0A]">
                        Interview Coins
                    </h1>
                    <p className="mt-2 text-sm text-black/45">
                        Use coins for Resume Scoring, Resume Builder, AI Interviews, and Roadmap Generation.
                    </p>
                </div>

                <div className="mt-8 grid place-items-center gap-3 md:grid-cols-2">
                    {plans.map((plan) => (
                        <PricingCard
                            key={plan.title}
                            {...plan}
                            onBuy={() => handlePayment(plan)}
                        />
                    ))}
                </div>

            </div>
        </div>

    );
}