import { client } from '@/client/index'

client.setConfig({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
})

export const setupAuthInterceptor = (getAccessToken: () => Promise<string>) => {
  client.instance.interceptors.request.use(async config => {
    try {
      const accessToken = await getAccessToken()
      config.headers.set('Authorization', `Bearer ${accessToken}`)
    } catch (error) {
      console.error('Failed to get access token:', error)
    }
    return config
  })
}
