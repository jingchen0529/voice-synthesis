/**
 * HTTP 请求封装
 */
import { message } from 'ant-design-vue'
import router from '@/router'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

interface RequestOptions extends RequestInit {
  timeout?: number
}

interface ApiResponse<T = unknown> {
  data: T
  message?: string
  code?: number
}

class HttpError extends Error {
  status: number
  data?: unknown

  constructor(message: string, status: number, data?: unknown) {
    super(message)
    this.status = status
    this.data = data
  }
}

// 获取 token
const getToken = (): string | null => {
  return localStorage.getItem('token')
}

// 请求拦截
const requestInterceptor = (options: RequestOptions): RequestOptions => {
  const token = getToken()
  const headers = new Headers(options.headers)

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  return { ...options, headers }
}

// 响应拦截
const responseInterceptor = async (response: Response): Promise<unknown> => {
  if (!response.ok) {
    let errorData: { detail?: string } = {}
    try {
      errorData = await response.json()
    } catch {
      // ignore
    }

    const errorMessage = errorData.detail || `请求失败: ${response.status}`

    // 401 未授权，跳转登录
    if (response.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      message.error('登录已过期，请重新登录')
      setTimeout(() => {
        window.location.href = '/auth?mode=login'
      }, 500)
    } else if (response.status === 403) {
      message.error(errorMessage)
    } else {
      message.error(errorMessage)
    }

    throw new HttpError(errorMessage, response.status, errorData)
  }

  // 处理空响应
  const contentType = response.headers.get('content-type')
  if (contentType?.includes('application/json')) {
    return response.json()
  }

  return response
}

// 通用请求方法
export const request = async <T>(
  url: string,
  options: RequestOptions = {}
): Promise<T> => {
  const fullUrl = url.startsWith('http') ? url : `${BASE_URL}${url}`
  const finalOptions = requestInterceptor(options)

  const response = await fetch(fullUrl, finalOptions)
  return responseInterceptor(response) as Promise<T>
}

// GET 请求
export const get = <T>(url: string, options?: RequestOptions): Promise<T> => {
  return request<T>(url, { ...options, method: 'GET' })
}

// POST 请求
export const post = <T>(
  url: string,
  data?: unknown,
  options?: RequestOptions
): Promise<T> => {
  const body = data instanceof FormData ? data : JSON.stringify(data)
  return request<T>(url, { ...options, method: 'POST', body })
}

// DELETE 请求
export const del = <T>(url: string, options?: RequestOptions): Promise<T> => {
  return request<T>(url, { ...options, method: 'DELETE' })
}

// PUT 请求
export const put = <T>(
  url: string,
  data?: unknown,
  options?: RequestOptions
): Promise<T> => {
  const body = data instanceof FormData ? data : JSON.stringify(data)
  return request<T>(url, { ...options, method: 'PUT', body })
}

export type { ApiResponse, HttpError }
