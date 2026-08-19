import { FiArrowLeft, FiZap } from "react-icons/fi";
import { useState, useEffect, useRef } from "react";
import DownloadButton from "./DownloadButton";
import ATSTemplate from "./ATSTemplate";
import AIResumeReviewModal from "./AIResumeReviewModal";
import { analyzeResumeData } from "../../api/resume.api";

export default function ResumePreview({ data, onBack , user , setUser }) {
  const resumeRef = useRef(null);
  const [scale, setScale] = useState(1);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);

  const handleAIReview = async () => {
    setReviewModalOpen(true);
    setReviewLoading(true);
    try {
      const res = await analyzeResumeData(data);
      if (res?.data) {
        setAnalysis(res.data);
      }
    } catch (err) {
      console.error("AI Review failed:", err);
      alert("Failed to analyze resume with AI. Please try again.");
    } finally {
      setReviewLoading(false);
    }
  };

useEffect(() => {
  const updateScale = () => {
    if (window.innerWidth < 640) {
      setScale(0.42);
    } else if (window.innerWidth < 768) {
      setScale(0.58);
    } else if (window.innerWidth < 1024) {
      setScale(0.72);
    } else {
      setScale(0.9);
    }
  };

  updateScale();

  window.addEventListener("resize", updateScale);

  return () =>
    window.removeEventListener("resize", updateScale);
}, []);

  return (
    <div className="min-h-screen bg-white text-[#0A0A0A]">
      <AIResumeReviewModal
        isOpen={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        loading={reviewLoading}
        analysis={analysis}
      />

      {/* Header */}
      <div className="sticky top-0 z-20 border-b border-black/8 bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-3 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">

          {/* Left */}
          <div>
            <h1 className="text-base font-bold sm:text-lg">
              Resume Preview
            </h1>

            <p className="mt-0.5 text-[10px] text-gray-400 sm:text-xs">
              Review your resume and analyze ATS readiness before downloading
            </p>
          </div>

          {/* Right */}
          <div className="flex items-center justify-between lg:justify-end gap-2.5">
            <button
              onClick={handleAIReview}
              className="flex h-8 items-center justify-center gap-1.5 rounded-lg border border-purple-500/30 bg-purple-500/10 px-2.5 sm:px-3 text-xs font-semibold text-purple-700 hover:bg-purple-500/20 transition"
            >
              <FiZap size={14} className="text-purple-600" />
              <span>AI ATS Review</span>
            </button>

            <button
              onClick={onBack}
              className="flex h-8 items-center justify-center gap-1.5 rounded-lg border border-black/15 px-2.5 sm:px-3 text-xs text-black/60 transition hover:border-black/35 hover:text-[#0A0A0A]"
            >
              <FiArrowLeft size={15} />

              <span className="hidden sm:block">
                Back to Edit
              </span>
            </button>

            <DownloadButton
              resumeRef={resumeRef}
              user={user}
              setUser={setUser}
            />
          </div>

        </div>
      </div>


      {/* Resume */}
      <div className="overflow-auto bg-[#F8F9FA] px-3 py-4 sm:px-6 sm:py-8">

  <div className="mx-auto flex justify-center">

   <div
  style={{
    transform: `scale(${scale})`,
    transformOrigin: "top center",
  }}
>
  <div
    ref={resumeRef}
    className="rounded-md bg-white shadow-[0_0_50px_rgba(0,0,0,.6)]"
  >
    <ATSTemplate data={data} />
  </div>
</div>

  </div>

</div>

    </div>
  );
}