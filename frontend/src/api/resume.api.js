import api from "../utils/axios";

/**
 * Fetch current user's saved/analyzed resume
 */
export const getResume = async () => {
  try {
    const response = await api.get("/api/resume/get-resume");
    return response.data;
  } catch (error) {
    console.warn("No existing resume found or failed to fetch:", error.response?.data || error.message);
    return null;
  }
};

/**
 * Upload and analyze PDF resume with AI ATS scanner
 */
export const uploadResume = async (formData) => {
  try {
    const response = await api.post("/api/resume/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Resume upload failed:", error.response?.data || error.message);
    throw error;
  }
};