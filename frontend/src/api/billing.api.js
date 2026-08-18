import api from "../utils/axios";

/**
 * Create a new Razorpay payment order for a coin subscription plan
 */
export const createPaymentOrder = async (data) => {
  try {
    const response = await api.post("/api/billing/create", data);
    return response.data;
  } catch (error) {
    console.error("Create payment order failed:", error.response?.data || error.message);
    throw error;
  }
};

/**
 * Verify Razorpay payment signature
 */
export const verifyPayment = async (data) => {
  try {
    const response = await api.post("/api/billing/verify", data);
    return response.data;
  } catch (error) {
    console.error("Verify payment failed:", error.response?.data || error.message);
    throw error;
  }
};

/**
 * Fetch past billing and transaction history for the user
 */
export const getPaymentHistory = async () => {
  try {
    const response = await api.get("/api/billing/history");
    return response.data;
  } catch (error) {
    console.error("Get payment history failed:", error.response?.data || error.message);
    return { success: false, history: [] };
  }
};
