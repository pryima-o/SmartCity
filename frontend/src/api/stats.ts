import { apiFetch } from "./config";

export const getStats = () => {
    return apiFetch("/v1/budget")
        .then((response) => {
        if (!response.ok) {
            throw new Error("Failed to fetch stats");
        }
        return response.json();
        })
        .catch((error) => {
        console.error(error);
});
}