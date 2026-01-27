import { client } from "./generated/client.gen";

client.setConfig({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
  withCredentials: true,
});

// TODO: set up interceptor for auth token when Auth0 is implemented
// export const setupAuthInterceptor = (getAccessToken: () => Promise<string>) => {
//   client.instance.interceptors.request.use(async config => {
//     try {
//       const accessToken = await getAccessToken()
//       config.headers.set('Authorization', `Bearer ${accessToken}`)
//     } catch (error) {
//       console.error('Failed to get access token:', error)
//     }
//     return config
//   })
// }
