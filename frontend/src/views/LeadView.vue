<template>
  <div class="p-4 lg:p-8">
    <div class="max-w-[1400px] mx-auto space-y-6">
      <!-- 筛选区域 -->
      <div
        class="bg-white/50 rounded-xl shadow-sm border border-slate-200/50 p-5 animate-fade-in-up"
        style="animation-delay: 100ms">
        <div class="flex flex-wrap items-center gap-4">
          <!-- 核心筛选组 -->
          <div class="flex items-center gap-2 p-1 rounded-lg border border-slate-200/50">
            <!-- 搜索 -->
            <div class="w-64">
              <a-input v-model:value="filters.keyword" placeholder="搜索名称、联系方式..."
                class="!border-0 !bg-transparent !shadow-none  rounded-md h-6 text-sm" @pressEnter="handleSearch">
                <template #prefix>
                  <Search :size="14" class="text-slate-400 mr-1" />
                </template>
              </a-input>
            </div>
          </div>

          <!-- 下拉筛选 -->
          <div class="flex items-center gap-3">
            <a-select v-model:value="filters.channel" class="min-w-[120px]" allow-clear placeholder="全部渠道">
              <template #suffixIcon><span class="text-slate-400">
                  <ChevronsUpDown :size="14" />
                </span></template>
              <a-select-option v-for="opt in options.channels" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </a-select-option>
            </a-select>

            <a-select v-model:value="filters.acquisitionType" class="min-w-[120px]" allow-clear placeholder="获客方式">
              <template #suffixIcon><span class="text-slate-400">
                  <ChevronsUpDown :size="14" />
                </span></template>
              <a-select-option v-for="opt in options.acquisition_types" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </a-select-option>
            </a-select>

            <!-- 日期筛选 Trigger -->
            <a-popover placement="bottomLeft" trigger="click" overlayClassName="date-filter-popover">
              <template #content>
                <div class="p-2 w-80">
                  <div class="mb-4">
                    <div class="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                      创建时间
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-2">
                      <button v-for="opt in dateShortcuts" :key="opt.value" @click="setCreatedDateRange(opt.value)"
                        :class="[
                          'px-2 py-1.5 text-xs rounded-md border transition-all',
                          createdDateType === opt.value
                            ? 'bg-emerald-50 border-emerald-200 text-emerald-600 font-medium'
                            : 'bg-white border-slate-100 text-slate-600 hover:border-slate-300',
                        ]">
                        {{ opt.label }}
                      </button>
                    </div>
                    <a-range-picker v-model:value="filters.createdRange" size="small" class="w-full"
                      :placeholder="['开始日期', '结束日期']" @change="createdDateType = 'custom'" />
                  </div>
                  <div>
                    <div class="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
                      更新时间
                    </div>
                    <div class="grid grid-cols-3 gap-2 mb-2">
                      <button v-for="opt in dateShortcuts" :key="opt.value" @click="setUpdatedDateRange(opt.value)"
                        :class="[
                          'px-2 py-1.5 text-xs rounded-md border transition-all',
                          updatedDateType === opt.value
                            ? 'bg-emerald-50 border-emerald-200 text-emerald-600 font-medium'
                            : 'bg-white border-slate-100 text-slate-600 hover:border-slate-300',
                        ]">
                        {{ opt.label }}
                      </button>
                    </div>
                    <a-range-picker v-model:value="filters.updatedRange" size="small" class="w-full"
                      :placeholder="['开始日期', '结束日期']" @change="updatedDateType = 'custom'" />
                  </div>
                </div>
              </template>
              <a-button
                class="!flex !items-center !gap-2 !text-slate-600 !border-slate-200 hover:!border-emerald-500 hover:!text-emerald-600">
                <Calendar :size="14" />
                <span class="text-xs">日期筛选</span>
              </a-button>
            </a-popover>
          </div>

          <div class="flex-1"></div>

          <!-- 统计 + 操作按钮 -->
          <div class="flex items-center gap-3">
            <!-- 统计卡片 -->
            <div
              class="hidden md:flex items-center gap-2 px-3 py-1.5 bg-white/80 rounded-lg border border-slate-200/50">
              <span class="text-xs text-slate-400">线索总数</span>
              <span class="text-sm font-bold text-emerald-600">{{
                stats.total.toLocaleString()
                }}</span>
            </div>

            <!-- 重置按钮 -->
            <a-button @click="resetFilters"
              class="!flex !items-center !justify-center !w-8 !h-8 !border-slate-300 !rounded-lg">
              <template #icon>
                <RotateCcw :size="15" stroke="#64748b" />
              </template>
            </a-button>

            <!-- 查询按钮 -->
            <a-button type="primary" @click="handleSearch"
              class="!flex !items-center !gap-1.5 !bg-emerald-500 hover:!bg-emerald-600 !border-0 !rounded-lg !h-8 !px-4">
              <Search :size="15" />
              <span class="text-sm">查询</span>
            </a-button>

            <!-- 新建任务按钮 -->
            <a-button type="primary" @click="showTaskModal = true"
              class="!flex !items-center !gap-1.5 !bg-slate-800 hover:!bg-slate-700 !border-0 !rounded-lg !h-8 !px-4">
              <Plus :size="15" />
              <span class="hidden md:inline text-sm">新建任务</span>
            </a-button>
          </div>
        </div>
      </div>

      <!-- 数据表格 -->
      <div
        class="bg-white/50 rounded-2xl border border-slate-200/50 shadow-sm overflow-hidden animate-fade-in-up"
        style="animation-delay: 200ms">
        <!-- 批量操作栏 -->
        <transition name="fade-slide">
          <div v-if="selectedRowKeys.length > 0"
            class="px-6 py-3 bg-emerald-50/80 backdrop-blur border-b border-emerald-100 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-2 h-2 rounded-full bg-emerald-500"></div>
              <span class="text-sm text-emerald-800 font-medium">
                已选择
                <span class="font-bold text-emerald-600 text-lg mx-1">{{
                  selectedRowKeys.length
                  }}</span>
                项数据
              </span>
            </div>
            <a-button danger size="small" @click="handleBatchDelete"
              class="!flex !items-center !gap-1.5 !bg-white !border-red-200 !text-red-500 hover:!bg-red-50 hover:!border-red-300 rounded-lg px-3 mb-0">
              <Trash2 :size="14" />
              批量删除
            </a-button>
          </div>
        </transition>

        <!-- 表格 -->
        <a-table :columns="columns" :data-source="leads" :loading="loading" :pagination="false"
          :row-selection="{ selectedRowKeys, onChange: onSelectChange }" :row-key="(record: Lead) => record.id"
          class="unique-table" :scroll="{ x: 1000 }">
          <!-- Namw -->
          <template #headerCell="{ column }">
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">{{
              column.title
              }}</span>
          </template>

          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'channel'">
              <div class="flex items-center gap-2">
                <div class="w-1.5 h-1.5 rounded-full" :style="{ background: getChannelColorValue(record.channel) }">
                </div>
                <span class="text-sm font-medium text-slate-700">{{ record.channel_label }}</span>
              </div>
            </template>

            <template v-else-if="column.key === 'acquisition_type'">
              <a-tag
                class="!bg-slate-100 !border-slate-200 !text-slate-500 !rounded-md !px-2 !text-xs !font-medium border-0">
                {{ record.acquisition_type_label }}
              </a-tag>
            </template>

            <template v-else-if="column.key === 'name'">
              <span class="text-sm font-semibold text-slate-700">{{ record.name || '-' }}</span>
            </template>

            <template v-else-if="column.key === 'contact'">
              <div v-if="record.contact" class="flex items-center gap-1.5 group cursor-pointer"
                @click="copyText(record.contact)">
                <span class="text-sm text-slate-600 font-mono group-hover:text-emerald-600 transition-colors">{{
                  record.contact }}</span>
              </div>
              <span v-else class="text-slate-300">-</span>
            </template>

            <template v-else-if="column.key === 'status'">
              <div :class="[
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
                getStatusClass(record.status),
              ]">
                {{ record.status_label }}
              </div>
            </template>

            <template v-else-if="column.key === 'created_at'">
              <div class="flex flex-col">
                <span class="text-xs font-medium text-slate-600">{{
                  dayjs(record.created_at).format('YYYY-MM-DD')
                  }}</span>
                <span class="text-[10px] text-slate-400">{{
                  dayjs(record.created_at).format('HH:mm')
                  }}</span>
              </div>
            </template>

            <template v-else-if="column.key === 'updated_at'">
              <span class="text-xs text-slate-400">{{ dayjs(record.updated_at).fromNow() }}</span>
            </template>

            <template v-else-if="column.key === 'action'">
              <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <a-tooltip title="访问来源">
                  <a-button type="text" size="small" :disabled="!record.source_url"
                    @click="openSourceUrl(record.source_url)"
                    class="!text-slate-400 hover:!text-blue-500 !w-8 !h-8 !rounded-lg flex items-center justify-center">
                    <ExternalLink :size="15" />
                  </a-button>
                </a-tooltip>
                <a-popconfirm title="确定要删除这条线索吗？" @confirm="handleDelete(record.id)" placement="topRight">
                  <template #icon>
                    <Trash2 class="text-red-500" :size="14" />
                  </template>
                  <a-button type="text" danger size="small"
                    class="!text-slate-400 hover:!text-red-500 hover:!bg-red-50 !w-8 !h-8 !rounded-lg flex items-center justify-center">
                    <Trash2 :size="15" />
                  </a-button>
                </a-popconfirm>
              </div>
            </template>
          </template>
        </a-table>

        <!-- 分页 -->
        <div class="px-6 py-4 border-t border-slate-200/30 flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400">共 {{ pagination.total }} 条</span>
          <a-pagination v-model:current="pagination.current" v-model:pageSize="pagination.pageSize"
            :total="pagination.total" :show-size-changer="true" :page-size-options="['10', '20', '50', '100']"
            size="small" @change="handlePageChange" @showSizeChange="handlePageSizeChange" />
        </div>
      </div>
    </div>

    <!-- 新建任务弹窗 -->
    <a-modal v-model:open="showTaskModal" title="新建获客任务" :width="520" :footer="null" :maskClosable="false" centered
      class="rounded-2xl overflow-hidden">
      <div class="pt-6 pb-2">
        <a-form :model="taskForm" layout="vertical" class="space-y-4">
          <div class="grid grid-cols-2 gap-5">
            <a-form-item label="目标渠道" required class="mb-0">
              <a-select v-model:value="taskForm.channel" placeholder="请选择" size="large" class="w-full">
                <a-select-option v-for="opt in options.channels" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="获客方式" required class="mb-0">
              <a-select v-model:value="taskForm.acquisitionType" placeholder="请选择" size="large">
                <a-select-option v-for="opt in options.acquisition_types" :key="opt.value" :value="opt.value">
                  {{ opt.label }}
                </a-select-option>
              </a-select>
            </a-form-item>
          </div>

          <a-form-item label="搜索关键词" required class="mb-0">
            <div class="relative">
              <a-input v-model:value="taskForm.keyword" placeholder="输入核心关键词，例如：'外贸'" size="large" class="!pl-9" />
              <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            </div>
            <p class="text-xs text-slate-400 mt-1.5">关键词越精准，获取到的线索质量越高</p>
          </a-form-item>

          <a-form-item label="预计采集数量" class="mb-0">
            <div class="flex items-center gap-4">
              <a-slider v-model:value="taskForm.count" :min="10" :max="100" class="flex-1" />
              <a-input-number v-model:value="taskForm.count" :min="1" :max="100" class="w-20" size="large" />
            </div>
          </a-form-item>

          <div class="flex items-center justify-end gap-3 mt-8 pt-4 border-t border-slate-100">
            <a-button size="large" @click="showTaskModal = false" class="!rounded-xl">取消</a-button>
            <a-button type="primary" size="large" @click="handleCreateTask" :loading="taskLoading"
              class="!bg-emerald-500 hover:!bg-emerald-600 !border-0 !shadow-lg !shadow-emerald-500/30 !rounded-xl !px-8">
              开始采集
            </a-button>
          </div>
        </a-form>
      </div>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  Users,
  Search,
  RotateCcw,
  Trash2,
  ExternalLink,
  Plus,
  ChevronsUpDown,
  Calendar,
} from 'lucide-vue-next'
import { leadApi, type Lead, type LeadOptions } from '@/api/lead'
import dayjs, { Dayjs } from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

// 筛选条件
const filters = reactive({
  channel: undefined as string | undefined,
  acquisitionType: undefined as string | undefined,
  keyword: '',
  createdRange: null as [Dayjs, Dayjs] | null,
  updatedRange: null as [Dayjs, Dayjs] | null,
})

// 日期快捷选项
const dateShortcuts = [
  { label: '今天', value: 'today' },
  { label: '昨天', value: 'yesterday' },
  { label: '近15天', value: 'last15days' },
]

const createdDateType = ref<string>('')
const updatedDateType = ref<string>('')
const showTaskModal = ref(false)
const taskLoading = ref(false)

// 新建任务表单
const taskForm = reactive({
  channel: undefined as string | undefined,
  acquisitionType: undefined as string | undefined,
  keyword: '',
  count: 50,
})

// 选项数据
const options = reactive<LeadOptions>({
  channels: [],
  acquisition_types: [],
  statuses: [],
})

// 表格数据
const leads = ref<Lead[]>([])
const loading = ref(false)
const selectedRowKeys = ref<number[]>([])

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
})

// 统计
const stats = reactive({
  total: 0,
})

// 表格列定义
const columns = [
  { title: '渠道', key: 'channel', dataIndex: 'channel', width: 140 },
  { title: '类型', key: 'acquisition_type', dataIndex: 'acquisition_type', width: 120 },
  { title: '名称', key: 'name', dataIndex: 'name', width: 180, ellipsis: true },
  { title: '联系方式', key: 'contact', dataIndex: 'contact', width: 200, ellipsis: true },
  { title: '状态', key: 'status', dataIndex: 'status', width: 100 },
  { title: '创建时间', key: 'created_at', dataIndex: 'created_at', width: 140 },
  { title: '最后更新', key: 'updated_at', dataIndex: 'updated_at', width: 120 },
  { title: '操作', key: 'action', width: 100, fixed: 'right', align: 'right' },
]

// 渠道颜色 helper (pure css/style value)
const getChannelColorValue = (channel: string) => {
  const colors: Record<string, string> = {
    google: '#3b82f6', // blue-500
    yahoo: '#a855f7', // purple-500
    tiktok: '#000000', // black
    facebook: '#1d4ed8', // blue-700
    youtube: '#ef4444', // red-500
    instagram: '#ec4899', // pink-500
    linkedin: '#0a66c2',
  }
  return colors[channel] || '#94a3b8' // slate-400
}

// 状态样式 helper
const getStatusClass = (status: number) => {
  const map: Record<number, string> = {
    0: 'bg-slate-100 text-slate-500 border-slate-200', // 待处理
    1: 'bg-blue-50 text-blue-600 border-blue-100', // 处理中
    2: 'bg-amber-50 text-amber-600 border-amber-100', // 潜在
    3: 'bg-emerald-50 text-emerald-600 border-emerald-100', // 转化
    4: 'bg-red-50 text-red-600 border-red-100', // 无效
  }
  return map[status] || 'bg-slate-100 text-slate-500 border-slate-200'
}

// 设置创建时间范围
const setCreatedDateRange = (type: string) => {
  createdDateType.value = type
  const today = dayjs().endOf('day')

  switch (type) {
    case 'today':
      filters.createdRange = [dayjs().startOf('day'), today]
      break
    case 'yesterday':
      filters.createdRange = [
        dayjs().subtract(1, 'day').startOf('day'),
        dayjs().subtract(1, 'day').endOf('day'),
      ]
      break
    case 'last15days':
      filters.createdRange = [dayjs().subtract(14, 'day').startOf('day'), today]
      break
  }
}

// 设置更新时间范围
const setUpdatedDateRange = (type: string) => {
  updatedDateType.value = type
  const today = dayjs().endOf('day')

  switch (type) {
    case 'today':
      filters.updatedRange = [dayjs().startOf('day'), today]
      break
    case 'yesterday':
      filters.updatedRange = [
        dayjs().subtract(1, 'day').startOf('day'),
        dayjs().subtract(1, 'day').endOf('day'),
      ]
      break
    case 'last15days':
      filters.updatedRange = [dayjs().subtract(14, 'day').startOf('day'), today]
      break
  }
}

// 加载选项
const loadOptions = async () => {
  try {
    const data = await leadApi.getOptions()
    options.channels = data.channels
    options.acquisition_types = data.acquisition_types
    options.statuses = data.statuses
  } catch (error) {
    console.error('加载选项失败:', error)
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params: Record<string, any> = {
      page: pagination.current,
      page_size: pagination.pageSize,
    }

    if (filters.channel) params.channel = filters.channel
    if (filters.acquisitionType) params.acquisition_type = filters.acquisitionType
    if (filters.keyword) params.keyword = filters.keyword

    if (filters.createdRange) {
      params.created_start = filters.createdRange[0].format('YYYY-MM-DD HH:mm:ss')
      params.created_end = filters.createdRange[1].format('YYYY-MM-DD HH:mm:ss')
    }

    if (filters.updatedRange) {
      params.updated_start = filters.updatedRange[0].format('YYYY-MM-DD HH:mm:ss')
      params.updated_end = filters.updatedRange[1].format('YYYY-MM-DD HH:mm:ss')
    }

    const data = await leadApi.getList(params)
    leads.value = data.items
    pagination.total = data.total
    stats.total = data.total
  } catch (error) {
    message.error('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.current = 1
  loadData()
}

// 重置筛选
const resetFilters = () => {
  filters.channel = undefined
  filters.acquisitionType = undefined
  filters.keyword = ''
  filters.createdRange = null
  filters.updatedRange = null
  createdDateType.value = ''
  updatedDateType.value = ''
  pagination.current = 1
  loadData()
}

// 分页变化
const handlePageChange = (page: number) => {
  pagination.current = page
  loadData()
}

const handlePageSizeChange = (_current: number, size: number) => {
  pagination.pageSize = size
  pagination.current = 1
  loadData()
}

// 选择变化
const onSelectChange = (keys: number[]) => {
  selectedRowKeys.value = keys
}

// 删除
const handleDelete = async (id: number) => {
  try {
    await leadApi.delete(id)
    message.success('删除成功')
    loadData()
  } catch (error) {
    message.error('删除失败')
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRowKeys.value.length === 0) return

  try {
    await leadApi.batchDelete(selectedRowKeys.value)
    message.success('批量删除成功')
    selectedRowKeys.value = []
    loadData()
  } catch (error) {
    message.error('批量删除失败')
  }
}

// 打开来源链接
const openSourceUrl = (url: string | null) => {
  if (url) {
    window.open(url, '_blank')
  }
}

// 复制文本
const copyText = (text: string) => {
  navigator.clipboard.writeText(text).then(() => {
    message.success('已复制到剪贴板')
  })
}

// 创建任务
const handleCreateTask = async () => {
  if (!taskForm.channel || !taskForm.acquisitionType || !taskForm.keyword) {
    message.warning('请填写完整信息')
    return
  }

  taskLoading.value = true
  try {
    // 这里模拟一下，实际应该调用API
    // await leadApi.createTask(taskForm)
    await new Promise((resolve) => setTimeout(resolve, 1000))
    message.success('任务创建成功，系统正在后台进行采集')
    showTaskModal.value = false
    // 重置表单
    taskForm.channel = undefined
    taskForm.acquisitionType = undefined
    taskForm.keyword = ''
    taskForm.count = 50
  } catch (error) {
    message.error('创建任务失败')
  } finally {
    taskLoading.value = false
  }
}

onMounted(() => {
  loadOptions()
  loadData()
})
</script>

<style scoped>
/* 自定义表格样式 */
.unique-table :deep(.ant-table) {
  background: transparent;
}

.unique-table :deep(.ant-table-thead > tr > th) {
  background: transparent;
  border-bottom: 1px solid rgba(226, 232, 240, 0.5);
  padding: 12px 16px;
}

.unique-table :deep(.ant-table-tbody > tr > td) {
  background: transparent;
  padding: 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.3);
  transition: all 0.3s;
}

.unique-table :deep(.ant-table-tbody > tr:hover > td) {
  background: rgba(255, 255, 255, 0.5);
}

/* 隐藏表格左右边框 */
.unique-table :deep(.ant-table-container) {
  border-radius: 0;
}

.unique-table :deep(.ant-table-placeholder) {
  background: transparent;
}

/* 动画 */
.animate-fade-in-down {
  animation: fadeInDown 0.6s ease-out forwards;
}

.animate-fade-in-up {
  animation: fadeInUp 0.6s ease-out forwards;
  opacity: 0;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 下拉菜单和日期选择器弹出层样式覆盖 */
:global(.date-filter-popover .ant-popover-inner) {
  border-radius: 12px;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.1);
  padding: 0;
  border: 1px solid #f1f5f9;
}

:global(.ant-select-selector) {
  border-radius: 8px !important;
  border-color: #e2e8f0 !important;
}

:global(.ant-select-focused .ant-select-selector) {
  border-color: #10b981 !important;
  /* emerald-500 */
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.1) !important;
}
</style>
