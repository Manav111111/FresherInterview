import api from "../utils/axios";

/**
 * Generate a new personalized career roadmap with AI
 */
export const generateRoadmap = async (data) => {
  try {
    const response = await api.post("/api/roadmap/generate", data);
    return response.data;
  } catch (error) {
    console.error("Generate roadmap failed:", error.response?.data || error.message);
    throw error;
  }
};

/**
 * Fetch all saved career roadmaps for the user
 */
export const getAllRoadmaps = async () => {
  try {
    const response = await api.get("/api/roadmap");
    return response.data;
  } catch (error) {
    console.error("Get roadmaps failed:", error.response?.data || error.message);
    return { success: false, data: [] };
  }
};

/**
 * Fetch a single career roadmap by ID
 */
export const getRoadmapById = async (id) => {
  try {
    const response = await api.get(`/api/roadmap/${id}`);
    return response.data;
  } catch (error) {
    console.error("Get roadmap by ID failed:", error.response?.data || error.message);
    return null;
  }
};
