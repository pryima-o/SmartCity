const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"
export const apiFetch = (endpoint: string, options: RequestInit = {}) => {
    return fetch(`${API_URL}${endpoint}`, {
        ...options,
        'headers': {
            'Content-Type': 'application/json',
            ...options.headers
        },

    })
}