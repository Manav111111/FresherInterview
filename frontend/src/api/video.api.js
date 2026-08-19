import api from "../utils/axios";

/**
 * Generate a structured educational whiteboard video solution for a question
 * @param {string} question
 * @returns {Promise<{success: boolean, data: Object}>}
 */
export const generateSolutionVideo = async (question) => {
  try {
    const response = await api.post("/api/video/generate-solution", {
      question: question.trim(),
    });
    return response.data;
  } catch (error) {
    console.error("Video solution generation failed:", error.response?.data || error.message);
    throw error;
  }
};
