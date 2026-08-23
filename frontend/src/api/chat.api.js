import api from "../utils/axios";

/**
 * Sends a message to the AI Chatbot with intent classification
 * @param {string} message - User message
 * @param {Array} history - Message history
 * @param {Object} context - User context (name, target_role)
 */
export const sendChatMessage = async (message, history = [], context = {}) => {
  try {
    const response = await api.post("/api/chat/message", {
      message,
      history,
      context,
    });
    return response.data;
  } catch (error) {
    console.error("Chat message error:", error.response?.data || error.message);
    return {
      success: false,
      reply: "I encountered an issue processing your request. Please try asking again in a moment.",
      intent: "general",
    };
  }
};
