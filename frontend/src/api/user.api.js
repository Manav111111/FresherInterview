import api from "../utils/axios";

/**
 * Fetch current authenticated user session and coin balance
 */
export const getCurrentUser = async () => {
  try {
    const response = await api.get("/api/me");
    return response.data;
  } catch (error) {
    console.warn("User not authenticated or session expired:", error.response?.data || error.message);
    return null;
  }
};

/**
 * Authenticate user with Firebase Google OAuth ID token
 */
export const loginWithFirebaseToken = async (token) => {
  try {
    const response = await api.post("/api/auth/login", { token });
    return response.data;
  } catch (error) {
    console.error("Login failed:", error.response?.data || error.message);
    throw error;
  }
};

/**
 * Log out user, delete Redis session, and clear session cookie
 */
export const logoutUser = async () => {
  try {
    const response = await api.get("/api/auth/logout");
    return response.data;
  } catch (error) {
    console.error("Logout error:", error.response?.data || error.message);
    return { success: false };
  }
};

/**
 * Deduct coins for an action (e.g. resume-score: 10, roadmap: 20, interview: 50)
 */
export const useCoins = async (data) => {
  try {
    const response = await api.post("/api/auth/use-interview-coins", data);
    return response.data;
  } catch (error) {
    console.error("Failed to use coins:", error.response?.data || error.message);
    throw error;
  }
};

/**
 * Add / credit interview coins to account
 */
export const addCoins = async (data) => {
  try {
    const response = await api.post("/api/auth/add-coins", data);
    return response.data;
  } catch (error) {
    console.error("Failed to add coins:", error.response?.data || error.message);
    throw error;
  }
};

