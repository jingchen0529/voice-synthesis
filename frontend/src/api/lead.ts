/**
 * 获客线索 API
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// 类型定义
export interface Lead {
  id: number
  channel: string
  channel_label: string
  acquisition_type: string
  acquisition_type_label: string
  name: string | null
  contact: string | null
  website: string | null
  description: string | null
  source_url: string | null
  source_keyword: string | null
  status: number
  status_label: string
  created_at: string
  updated_at: string
}

export interface LeadListResponse {
  total: number
  page: number
  page_size: number
  items: Lead[]
}

export interface LeadOptions {
  channels: { value: string; label: string }[]
  acquisition_types: { value: string; label: string }[]
  statuses: { value: number; label: string }[]
}

export interface LeadListParams {
  page?: number
  page_size?: number
  channel?: string
  acquisition_type?: string
  keyword?: string
  status?: number
  created_start?: string
  created_end?: string
  updated_start?: string
  updated_end?: string
}

export interface LeadCreate {
  channel: string
  acquisition_type: string
  name?: string
  contact?: string
  website?: string
  description?: string
  source_url?: string
  source_keyword?: string
  status?: number
}

export interface LeadStats {
  total: number
  by_channel: Record<string, number>
  by_type: Record<string, number>
  by_status: Record<number, number>
}

// API 方法
export const leadApi = {
  // 获取筛选选项
  getOptions: async (): Promise<LeadOptions> => {
    const response = await fetch(`${BASE_URL}/lead/options`)
    if (!response.ok) throw new Error('获取选项失败')
    return response.json()
  },

  // 获取线索列表
  getList: async (params: LeadListParams = {}): Promise<LeadListResponse> => {
    const searchParams = new URLSearchParams()
    
    if (params.page) searchParams.append('page', params.page.toString())
    if (params.page_size) searchParams.append('page_size', params.page_size.toString())
    if (params.channel) searchParams.append('channel', params.channel)
    if (params.acquisition_type) searchParams.append('acquisition_type', params.acquisition_type)
    if (params.keyword) searchParams.append('keyword', params.keyword)
    if (params.status !== undefined) searchParams.append('status', params.status.toString())
    if (params.created_start) searchParams.append('created_start', params.created_start)
    if (params.created_end) searchParams.append('created_end', params.created_end)
    if (params.updated_start) searchParams.append('updated_start', params.updated_start)
    if (params.updated_end) searchParams.append('updated_end', params.updated_end)

    const response = await fetch(`${BASE_URL}/lead/list?${searchParams.toString()}`)
    if (!response.ok) throw new Error('获取列表失败')
    return response.json()
  },

  // 获取单条线索
  getDetail: async (id: number): Promise<Lead> => {
    const response = await fetch(`${BASE_URL}/lead/${id}`)
    if (!response.ok) throw new Error('获取详情失败')
    return response.json()
  },

  // 创建线索
  create: async (data: LeadCreate): Promise<Lead> => {
    const response = await fetch(`${BASE_URL}/lead/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '创建失败')
    }
    return response.json()
  },

  // 更新线索
  update: async (id: number, data: Partial<LeadCreate>): Promise<Lead> => {
    const response = await fetch(`${BASE_URL}/lead/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '更新失败')
    }
    return response.json()
  },

  // 删除线索
  delete: async (id: number): Promise<void> => {
    const response = await fetch(`${BASE_URL}/lead/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) throw new Error('删除失败')
  },

  // 批量删除
  batchDelete: async (ids: number[]): Promise<{ deleted_count: number }> => {
    const response = await fetch(`${BASE_URL}/lead/batch-delete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids }),
    })
    if (!response.ok) throw new Error('批量删除失败')
    return response.json()
  },

  // 获取统计摘要
  getStats: async (): Promise<LeadStats> => {
    const response = await fetch(`${BASE_URL}/lead/stats/summary`)
    if (!response.ok) throw new Error('获取统计失败')
    return response.json()
  },
}
