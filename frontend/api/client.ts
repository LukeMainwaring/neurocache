import { client } from "./generated/client.gen";

client.setConfig({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
  withCredentials: true,
});

export const setupAuthInterceptor = (getAccessToken: () => Promise<string>) => {
  client.instance.interceptors.request.use(async (config) => {
    try {
      const accessToken = await getAccessToken();
      config.headers.set("Authorization", `Bearer ${accessToken}`);
    } catch (error) {
      console.error("Failed to get access token:", error);
    }
    return config;
  });
};

let _getAccessToken: (() => Promise<string>) | null = null;

export const setAccessTokenGetter = (fn: () => Promise<string>) => {
  _getAccessToken = fn;
};

export const getAccessToken = async (): Promise<string | null> => {
  if (!_getAccessToken) return null;
  try {
    return await _getAccessToken();
  } catch {
    return null;
  }
};
