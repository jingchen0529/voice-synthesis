/**
 * 认证相关 API
 */
import { post, get, put } from '../utils/request'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: number
    username: string
    email: string
    nickname: string
  }
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  nickname?: string
}

export interface RegisterResponse {
  message: string
  user_id: number
}

export interface UserInfo {
  id: number
  username: string
  email: string
  nickname: string
  avatar?: string
  quotas: QuotaInfo[]
  remaining_uses: number
}

export interface QuotaInfo {
  service_code: string
  service_name: string
  free_quota: number
  paid_quota: number
  total: number
}

export interface ApiKeyInfo {
  id: number
  access_key: string
  status: number
  created_at: string
}

export interface ApiKeyResponse {
  access_key: string
  secret_key: string
  message: string
}

export const authApi = {
  login: (data: LoginRequest) => post<LoginResponse>('/auth/login', data),
  register: (data: RegisterRequest) => post<RegisterResponse>('/auth/register', data),
  getMe: () => get<UserInfo>('/auth/me'),
  
  // API 密钥
  getApiKey: () => get<ApiKeyInfo | null>('/auth/api-key'),
  createApiKey: () => post<ApiKeyResponse>('/auth/api-key'),
  regenerateApiKey: () => put<ApiKeyResponse>('/auth/api-key'),
}
