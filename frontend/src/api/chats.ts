import { apiFetch } from "./config";
export const chatsApi = {
  create: async (q: string, c: string) => {
    try {
      if (q.length === 0) {
        return 0;
      }

      const response = await apiFetch("/v1/chats", {
        method: "POST",
        body: JSON.stringify({
          query: q,
          categoryId: c,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to create chat");
      }

      const data = await response.json();
      console.log(data);

      return data;
    } catch (error) {
      console.error(error);
    }
  },

  get: async (chatId: string) => {
    try {
      const response = await apiFetch(`/v1/chats/${chatId}`);

      if (!response.ok) {
        throw new Error("Failed to fetch chat");
      }

      return await response.json();
    } catch (error) {
      console.error(error);
    }
  },

  getMessages: async (chatId: string) => {
    try {
      const response = await apiFetch(`/v1/chats/${chatId}/messages`);

      if (!response.ok) {
        throw new Error("Failed to fetch messages");
      }

      return await response.json();
    } catch (error) {
      console.error(error);
    }
  },

  sendMessage: async (chatId: string, content: string) => {
    try {
      if (!content.trim()) {
        return null;
      }

      const response = await apiFetch(
        `/v1/chats/${chatId}/messages`,
        {
          method: "POST",
          body: JSON.stringify({
            content,
          }),
        },
      );

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      return await response.json();
    } catch (error) {
      console.error(error);
      return null;
    }
  },
};