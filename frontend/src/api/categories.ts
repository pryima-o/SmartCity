import { ref } from "vue";
import { apiFetch } from "./config";

const localCategories = ref<any[]>([]);

export const categoriesApi = {
  list: async () => {
    try {
      if (localCategories.value.length > 0) {
        return localCategories.value;
      }
      const response = await apiFetch("/v1/categories");
      if (!response.ok) {
        throw new Error("Failed to fetch categories");
      }
      const data = await response.json();
      localCategories.value = data;
      return localCategories.value;
    } catch (error) {
      console.error(error);
    }
  },
};
