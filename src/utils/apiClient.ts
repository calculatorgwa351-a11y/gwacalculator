import router from '@/router'
import { useAuthStore } from '@/stores/auth'
import { useSessionStore } from '@/stores/session'

type ApiFetchOptions = RequestInit & { json?: unknown; skipAuthError?: boolean }

export const apiFetch = async (input: RequestInfo | URL, options: ApiFetchOptions = {}) => {
  const { json, headers, ...rest } = options
  const mergedHeaders: HeadersInit = {
    ...(json ? { 'Content-Type': 'application/json' } : {}),
    ...(headers || {})
  }

  const res = await fetch(input, {
    ...rest,
    credentials: 'include',
    headers: mergedHeaders,
    body: json ? JSON.stringify(json) : rest.body
  })

  if (res.status === 401 && !options.skipAuthError) {
    const auth = useAuthStore()
    const session = useSessionStore()
    auth.handleUnauthorized()
    session.setExpired()

    if (router.currentRoute.value.path !== '/') {
      router.push('/')
    }
  }

  return res
}
