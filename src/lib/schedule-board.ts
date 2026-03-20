import {
  acknowledgeSchedule,
  completeSchedule,
  createSchedule,
  deleteSchedule,
  listSchedules,
  rescheduleSchedule,
  snoozeSchedule,
  updateSchedule,
  type ScheduleItem,
  type SchedulePayload,
} from './api/client';
import { recordAction, setPageContext } from './runtime-context';

const POLL_INTERVAL = 30_000;
const NOTIFICATION_SCAN_INTERVAL = 15_000;
const DEFAULT_SNOOZE_MINUTES = 10;
const DEFAULT_SCOPE_LABEL = '默认知识库';

type NotificationPermissionState = NotificationPermission | 'unsupported';
type RenderMode = 'active' | 'completed';

type DomRefs = {
  feedback: HTMLDivElement;
  notificationStatus: HTMLParagraphElement;
  requestNotification: HTMLButtonElement;
  todayList: HTMLDivElement;
  upcomingList: HTMLDivElement;
  completedList: HTMLDivElement;
  statActive: HTMLParagraphElement;
  statToday: HTMLParagraphElement;
  statCompleted: HTMLParagraphElement;
  statRecurring: HTMLParagraphElement;
  formCard: HTMLElement;
  form: HTMLFormElement;
  formTitle: HTMLHeadingElement;
  formModeBadge: HTMLSpanElement;
  submitButton: HTMLButtonElement;
  cancelEdit: HTMLButtonElement;
  refreshSchedules: HTMLButtonElement;
  scrollToForm: HTMLButtonElement;
  title: HTMLInputElement;
  description: HTMLTextAreaElement;
  scheduledFor: HTMLInputElement;
  reminderOffsetMinutes: HTMLSelectElement;
  repeatRule: HTMLSelectElement;
};

const state: {
  schedules: ScheduleItem[];
  editingId: number | null;
  fetchTimer: number | null;
  notificationTimer: number | null;
  isSubmitting: boolean;
  pendingAcks: Set<number>;
  notificationPermission: NotificationPermissionState;
} = {
  schedules: [],
  editingId: null,
  fetchTimer: null,
  notificationTimer: null,
  isSubmitting: false,
  pendingAcks: new Set<number>(),
  notificationPermission:
    typeof window !== 'undefined' && 'Notification' in window
      ? Notification.permission
      : 'unsupported',
};

function mustElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing required element: #${id}`);
  }
  return element as T;
}

const dom: DomRefs = {
  feedback: mustElement<HTMLDivElement>('feedback'),
  notificationStatus: mustElement<HTMLParagraphElement>('notification-status'),
  requestNotification: mustElement<HTMLButtonElement>('request-notification'),
  todayList: mustElement<HTMLDivElement>('today-list'),
  upcomingList: mustElement<HTMLDivElement>('upcoming-list'),
  completedList: mustElement<HTMLDivElement>('completed-list'),
  statActive: mustElement<HTMLParagraphElement>('stat-active'),
  statToday: mustElement<HTMLParagraphElement>('stat-today'),
  statCompleted: mustElement<HTMLParagraphElement>('stat-completed'),
  statRecurring: mustElement<HTMLParagraphElement>('stat-recurring'),
  formCard: mustElement<HTMLElement>('schedule-form-card'),
  form: mustElement<HTMLFormElement>('schedule-form'),
  formTitle: mustElement<HTMLHeadingElement>('form-title'),
  formModeBadge: mustElement<HTMLSpanElement>('form-mode-badge'),
  submitButton: mustElement<HTMLButtonElement>('submit-button'),
  cancelEdit: mustElement<HTMLButtonElement>('cancel-edit'),
  refreshSchedules: mustElement<HTMLButtonElement>('refresh-schedules'),
  scrollToForm: mustElement<HTMLButtonElement>('scroll-to-form'),
  title: mustElement<HTMLInputElement>('schedule-title'),
  description: mustElement<HTMLTextAreaElement>('schedule-description'),
  scheduledFor: mustElement<HTMLInputElement>('schedule-datetime'),
  reminderOffsetMinutes: mustElement<HTMLSelectElement>('schedule-reminder'),
  repeatRule: mustElement<HTMLSelectElement>('schedule-repeat'),
};

function escapeHtml(text: unknown): string {
  return String(text ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function nl2br(text: string): string {
  return escapeHtml(text).replaceAll('\n', '<br />');
}

function setFeedback(message: string, tone: 'info' | 'success' | 'error' = 'info') {
  if (!message) {
    dom.feedback.className =
      'hidden mt-8 rounded-md border px-4 py-3 text-sm font-light leading-relaxed';
    dom.feedback.textContent = '';
    return;
  }

  const toneClasses: Record<'info' | 'success' | 'error', string> = {
    info: 'border-slate-100 bg-white/80 text-slate-600',
    success: 'border-brand-blue/30 bg-brand-surface/30 text-slate-700',
    error: 'border-brand-sand/60 bg-brand-sand/35 text-slate-700',
  };

  dom.feedback.className = `mt-8 rounded-md border px-4 py-3 text-sm font-light leading-relaxed ${
    toneClasses[tone]
  }`;
  dom.feedback.textContent = message;
}

function getNextHalfHour(): Date {
  const date = new Date();
  date.setSeconds(0, 0);
  const minutes = date.getMinutes();
  if (minutes === 0 || minutes === 30) {
    date.setMinutes(minutes + 30);
  } else if (minutes < 30) {
    date.setMinutes(30);
  } else {
    date.setHours(date.getHours() + 1, 0, 0, 0);
  }
  return date;
}

function toLocalInputValue(dateLike: string | Date): string {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(date.getTime())) return '';
  const offset = date.getTimezoneOffset();
  const localDate = new Date(date.getTime() - offset * 60_000);
  return localDate.toISOString().slice(0, 16);
}

function formatDateTime(dateLike: string | Date): string {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(date.getTime())) return '时间无效';
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatFullDateTime(dateLike: string | Date): string {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(date.getTime())) return '时间无效';
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatTimeLabel(dateLike: string | Date): string {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(date.getTime())) return '--:--';
  return new Intl.DateTimeFormat('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function formatDayLabel(dateLike: string | Date): string {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(date.getTime())) return '时间无效';

  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);
  const dayAfterTomorrow = new Date(tomorrow);
  dayAfterTomorrow.setDate(dayAfterTomorrow.getDate() + 1);
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date >= today && date < tomorrow) return '今天';
  if (date >= tomorrow && date < dayAfterTomorrow) return '明天';
  if (date >= yesterday && date < today) return '昨天';

  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    weekday: 'short',
  }).format(date);
}

function getRepeatLabel(rule: ScheduleItem['repeatRule']): string {
  switch (rule) {
    case 'daily':
      return '每天';
    case 'weekdays':
      return '工作日';
    case 'weekly':
      return '每周';
    default:
      return '单次';
  }
}

function getEffectiveTime(schedule: ScheduleItem): string {
  return schedule.snoozedUntil || schedule.scheduledFor;
}

function getTimelineTime(schedule: ScheduleItem, mode: RenderMode): string {
  if (mode === 'completed') {
    return schedule.lastCompletedAt || schedule.scheduledFor;
  }
  return getEffectiveTime(schedule);
}

function getScopeLabel(schedule: ScheduleItem): string {
  return schedule.projectId === 1 ? DEFAULT_SCOPE_LABEL : `项目 ${schedule.projectId}`;
}

function isBeforeTomorrow(dateLike: string | Date): boolean {
  const date = dateLike instanceof Date ? dateLike : new Date(dateLike);
  if (Number.isNaN(date.getTime())) return false;
  const tomorrow = new Date();
  tomorrow.setHours(24, 0, 0, 0);
  return date.getTime() < tomorrow.getTime();
}

function getSortedSchedules(items: ScheduleItem[]): ScheduleItem[] {
  return [...items].sort(
    (a, b) => new Date(getEffectiveTime(a)).getTime() - new Date(getEffectiveTime(b)).getTime()
  );
}

function renderEmptyState(message: string): string {
  return `
    <div class="py-8">
      <div class="rounded-md border border-dashed border-slate-100 bg-brand-cream/45 px-4 py-6 text-sm font-light leading-relaxed text-slate-500">
        ${escapeHtml(message)}
      </div>
    </div>
  `;
}

function renderReminderLine(schedule: ScheduleItem): string {
  if (schedule.snoozedUntil) {
    return `已延后至 ${formatFullDateTime(schedule.snoozedUntil)}`;
  }
  if ((schedule.reminderOffsetMinutes || 0) > 0) {
    return `提醒于 ${formatFullDateTime(
      schedule.nextTriggerAt || schedule.scheduledFor
    )} · 提前 ${schedule.reminderOffsetMinutes} 分钟`;
  }
  return `提醒于 ${formatFullDateTime(schedule.nextTriggerAt || schedule.scheduledFor)}`;
}

function renderMetaItems(items: string[]): string {
  return items
    .map((item) => `<span class="inline-flex items-center">${escapeHtml(item)}</span>`)
    .join('<span class="text-slate-300">·</span>');
}

function renderActionButton(
  action: string,
  scheduleId: number,
  label: string,
  tone: 'default' | 'accent' = 'default'
): string {
  const toneClasses =
    tone === 'accent'
      ? 'text-slate-700 hover:border-brand-blue/35 hover:bg-brand-surface/35'
      : 'text-slate-500 hover:border-slate-200 hover:bg-white/90 hover:text-slate-700';

  return `
    <button
      data-action="${action}"
      data-id="${scheduleId}"
      class="inline-flex items-center gap-1 rounded-md border border-transparent px-2.5 py-1.5 text-xs tracking-tight transition ${toneClasses}"
    >
      ${escapeHtml(label)}
    </button>
  `;
}

function renderStatusNode(mode: RenderMode, index: number, total: number): string {
  const line =
    index < total - 1
      ? '<span class="absolute left-1/2 top-4 h-[calc(100%+1.75rem)] w-px -translate-x-1/2 bg-slate-100"></span>'
      : '';

  const node =
    mode === 'completed'
      ? `
        <span class="relative z-10 mt-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-400">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-2.5 w-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="m5 13 4 4L19 7" />
          </svg>
        </span>
      `
      : `
        <span class="relative z-10 mt-1 inline-flex h-4 w-4 items-center justify-center rounded-full border border-brand-blue/25 bg-white">
          <span class="h-1.5 w-1.5 rounded-full bg-brand-blue"></span>
        </span>
      `;

  return `${line}${node}`;
}

function renderScheduleEntry(
  schedule: ScheduleItem,
  mode: RenderMode,
  index: number,
  total: number
): string {
  const timelineTime = new Date(getTimelineTime(schedule, mode));
  const effectiveTime = new Date(getEffectiveTime(schedule));
  const isOverdue =
    mode !== 'completed' &&
    !Number.isNaN(effectiveTime.getTime()) &&
    effectiveTime.getTime() < Date.now();

  const metaItems =
    mode === 'completed'
      ? [
          `完成于 ${formatFullDateTime(schedule.lastCompletedAt || schedule.scheduledFor)}`,
          `原定 ${formatFullDateTime(schedule.scheduledFor)}`,
          `重复 · ${getRepeatLabel(schedule.repeatRule)}`,
        ]
      : [
          renderReminderLine(schedule),
          `计划于 ${formatFullDateTime(schedule.scheduledFor)}`,
          `重复 · ${getRepeatLabel(schedule.repeatRule)}`,
        ];

  if (isOverdue) {
    metaItems.unshift('已到期，建议优先处理');
  }

  const description = schedule.description
    ? `<p class="mt-2 text-sm font-light leading-relaxed text-slate-500">${nl2br(
        schedule.description
      )}</p>`
    : '';

  const actionButtons =
    mode === 'completed'
      ? [
          renderActionButton('edit', schedule.id, '编辑'),
          renderActionButton('delete', schedule.id, '删除'),
        ].join('')
      : [
          renderActionButton(
            'complete',
            schedule.id,
            schedule.isRecurring ? '完成本次' : '完成',
            'accent'
          ),
          renderActionButton('snooze', schedule.id, `延后 ${DEFAULT_SNOOZE_MINUTES} 分钟`),
          renderActionButton('reschedule', schedule.id, '改期'),
          renderActionButton('edit', schedule.id, '编辑'),
          renderActionButton('delete', schedule.id, '删除'),
        ].join('');

  const dividerClass = index < total - 1 ? 'border-b border-slate-100' : '';

  return `
    <article class="relative grid gap-x-4 gap-y-3 py-6 sm:grid-cols-[88px_22px_minmax(0,1fr)] ${dividerClass}">
      <div class="pt-0.5 text-right">
        <p class="text-sm font-normal tracking-tight text-slate-400">${escapeHtml(
          formatTimeLabel(timelineTime)
        )}</p>
        <p class="mt-1 text-[11px] font-light tracking-tight text-slate-400">${escapeHtml(
          formatDayLabel(timelineTime)
        )}</p>
      </div>

      <div class="relative flex justify-center">
        ${renderStatusNode(mode, index, total)}
      </div>

      <div class="min-w-0">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div class="min-w-0 max-w-2xl">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="text-base font-normal tracking-tight text-slate-700">${escapeHtml(
                schedule.title
              )}</h3>
              <span class="inline-flex items-center rounded-md bg-brand-surface/45 px-2.5 py-1 text-[11px] font-light tracking-tight text-slate-500">${escapeHtml(
                getScopeLabel(schedule)
              )}</span>
            </div>
            ${description}
            <div class="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1 text-[12px] font-light tracking-tight text-slate-400">
              ${renderMetaItems(metaItems)}
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-1.5 lg:max-w-[260px] lg:justify-end">
            ${actionButtons}
          </div>
        </div>
      </div>
    </article>
  `;
}

function renderScheduleList(items: ScheduleItem[], mode: RenderMode = 'active'): string {
  return items.map((schedule, index) => renderScheduleEntry(schedule, mode, index, items.length)).join('');
}

function renderScheduleSections() {
  const activeSchedules = getSortedSchedules(
    state.schedules.filter((schedule) => schedule.status !== 'completed')
  );
  const todaySchedules = activeSchedules.filter((schedule) =>
    isBeforeTomorrow(getEffectiveTime(schedule))
  );
  const upcomingSchedules = activeSchedules.filter(
    (schedule) => !isBeforeTomorrow(getEffectiveTime(schedule))
  );
  const completedSchedules = [...state.schedules]
    .filter((schedule) => schedule.status === 'completed')
    .sort(
      (a, b) =>
        new Date(b.lastCompletedAt || b.scheduledFor).getTime() -
        new Date(a.lastCompletedAt || a.scheduledFor).getTime()
    );

  dom.todayList.innerHTML = todaySchedules.length
    ? renderScheduleList(todaySchedules)
    : renderEmptyState('今天还没有待处理任务。可以从右侧先创建一条轻量日程。');

  dom.upcomingList.innerHTML = upcomingSchedules.length
    ? renderScheduleList(upcomingSchedules)
    : renderEmptyState('还没有未来任务。重复模板也会沿着这条时间轴继续展开。');

  dom.completedList.innerHTML = completedSchedules.length
    ? renderScheduleList(completedSchedules, 'completed')
    : renderEmptyState('暂无完成记录。完成一次任务后，这里会留下灰度化的执行痕迹。');

  dom.statActive.textContent = String(activeSchedules.length);
  dom.statToday.textContent = String(todaySchedules.length);
  dom.statCompleted.textContent = String(completedSchedules.length);
  dom.statRecurring.textContent = String(
    state.schedules.filter((schedule) => schedule.isRecurring).length
  );
}

function updateNotificationUI() {
  const permission = state.notificationPermission;
  const mapping: Record<NotificationPermissionState, string> = {
    granted: '已开启，任务到点后会发送浏览器提醒。',
    denied: '已拒绝，请在浏览器站点权限中手动重新允许通知。',
    default: '尚未开启，可点击右侧按钮授权。',
    unsupported: '当前浏览器不支持桌面通知，请改用支持 Notification API 的浏览器。',
  };

  dom.notificationStatus.textContent = mapping[permission] || '状态未知';
  dom.requestNotification.disabled = permission === 'granted' || permission === 'unsupported';
  dom.requestNotification.textContent = permission === 'granted' ? '已开启' : '开启提醒';
}

function resetForm() {
  state.editingId = null;
  dom.form.reset();
  dom.formTitle.textContent = '新建任务';
  dom.formModeBadge.textContent = '新建';
  dom.submitButton.textContent = '保存任务';
  dom.cancelEdit.classList.add('hidden');
  dom.scheduledFor.value = toLocalInputValue(getNextHalfHour());
  dom.reminderOffsetMinutes.value = '0';
  dom.repeatRule.value = 'none';
}

function fillForm(schedule: ScheduleItem) {
  state.editingId = schedule.id;
  dom.formTitle.textContent = '编辑任务';
  dom.formModeBadge.textContent = '编辑中';
  dom.submitButton.textContent = '保存更改';
  dom.cancelEdit.classList.remove('hidden');
  dom.title.value = schedule.title || '';
  dom.description.value = schedule.description || '';
  dom.scheduledFor.value = toLocalInputValue(schedule.scheduledFor);
  dom.reminderOffsetMinutes.value = String(schedule.reminderOffsetMinutes || 0);
  dom.repeatRule.value = schedule.repeatRule || 'none';
  dom.formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function buildPayloadFromForm(): SchedulePayload {
  const localValue = dom.scheduledFor.value;
  const parsedDate = new Date(localValue);
  if (!localValue || Number.isNaN(parsedDate.getTime())) {
    throw new Error('请填写有效的执行时间。');
  }

  return {
    title: dom.title.value.trim(),
    description: dom.description.value.trim(),
    scheduledFor: parsedDate.toISOString(),
    reminderOffsetMinutes: Number(dom.reminderOffsetMinutes.value || 0),
    repeatRule: (dom.repeatRule.value || 'none') as ScheduleItem['repeatRule'],
  };
}

function replaceSchedule(nextSchedule: ScheduleItem) {
  const nextIndex = state.schedules.findIndex((item) => item.id === nextSchedule.id);
  if (nextIndex >= 0) {
    state.schedules.splice(nextIndex, 1, nextSchedule);
  } else {
    state.schedules.push(nextSchedule);
  }
  renderScheduleSections();
}

async function refreshSchedules({ silent = false }: { silent?: boolean } = {}) {
  try {
    const schedules = await listSchedules();
    state.schedules = schedules;
    renderScheduleSections();
    recordAction('schedules_loaded', { scheduleCount: schedules.length });
    if (!silent) {
      setFeedback('日程数据已刷新。', 'info');
    }
  } catch (error) {
    console.error(error);
    setFeedback(error instanceof Error ? error.message : '加载日程失败。', 'error');
  }
}

async function handleSubmit(event: SubmitEvent) {
  event.preventDefault();
  if (state.isSubmitting) return;

  const wasEditing = state.editingId !== null;

  try {
    const payload = buildPayloadFromForm();
    if (!payload.title) {
      throw new Error('任务标题不能为空。');
    }

    state.isSubmitting = true;
    dom.submitButton.disabled = true;

    const schedule = state.editingId
      ? await updateSchedule(state.editingId, payload)
      : await createSchedule(payload);

    recordAction(wasEditing ? 'schedule_updated' : 'schedule_created', {
      scheduleId: String(schedule.id),
      scheduleTitle: schedule.title,
    });
    replaceSchedule(schedule);
    resetForm();
    setFeedback(wasEditing ? '任务已更新。' : '任务已创建。', 'success');

    if (state.notificationPermission === 'granted') {
      await checkDueNotifications();
    }
  } catch (error) {
    console.error(error);
    setFeedback(error instanceof Error ? error.message : '保存失败。', 'error');
  } finally {
    state.isSubmitting = false;
    dom.submitButton.disabled = false;
  }
}

async function handleAction(action: string, scheduleId: number) {
  const schedule = state.schedules.find((item) => item.id === scheduleId);
  if (!schedule) return;

  try {
    if (action === 'edit') {
      fillForm(schedule);
      return;
    }

    if (action === 'delete') {
      const confirmed = window.confirm(`确认删除「${schedule.title}」吗？`);
      if (!confirmed) return;
      await deleteSchedule(scheduleId);
      recordAction('schedule_deleted', {
        scheduleId: String(scheduleId),
        scheduleTitle: schedule.title,
      });
      state.schedules = state.schedules.filter((item) => item.id !== scheduleId);
      renderScheduleSections();
      setFeedback('任务已删除。', 'success');
      if (state.editingId === scheduleId) {
        resetForm();
      }
      return;
    }

    if (action === 'complete') {
      const nextSchedule = await completeSchedule(scheduleId);
      recordAction('schedule_completed', {
        scheduleId: String(scheduleId),
        scheduleTitle: schedule.title,
      });
      replaceSchedule(nextSchedule);
      setFeedback(
        schedule.isRecurring ? '本次任务已完成，系统已自动排入下一次。' : '任务已完成。',
        'success'
      );
      return;
    }

    if (action === 'snooze') {
      const nextSchedule = await snoozeSchedule(scheduleId, DEFAULT_SNOOZE_MINUTES);
      recordAction('schedule_snoozed', {
        scheduleId: String(scheduleId),
        scheduleTitle: schedule.title,
      });
      replaceSchedule(nextSchedule);
      setFeedback(`任务已延后 ${DEFAULT_SNOOZE_MINUTES} 分钟。`, 'success');
      return;
    }

    if (action === 'reschedule') {
      const defaultValue = toLocalInputValue(schedule.scheduledFor);
      const nextValue = window.prompt(
        '请输入新的时间（格式：YYYY-MM-DDTHH:MM）',
        defaultValue
      );
      if (!nextValue) return;
      const nextDate = new Date(nextValue);
      if (Number.isNaN(nextDate.getTime())) {
        throw new Error('改期时间格式不正确。');
      }
      const nextSchedule = await rescheduleSchedule(scheduleId, nextDate.toISOString());
      recordAction('schedule_rescheduled', {
        scheduleId: String(scheduleId),
        scheduleTitle: schedule.title,
      });
      replaceSchedule(nextSchedule);
      setFeedback('任务已改期。', 'success');
    }
  } catch (error) {
    console.error(error);
    setFeedback(error instanceof Error ? error.message : '操作失败。', 'error');
  }
}

function createNotificationBody(schedule: ScheduleItem): string {
  const pieces = [`计划时间：${formatDateTime(schedule.scheduledFor)}`];
  if (schedule.description) {
    pieces.push(schedule.description);
  }
  if (schedule.isRecurring) {
    pieces.push(`重复：${getRepeatLabel(schedule.repeatRule)}`);
  }
  return pieces.join(' · ');
}

function notifySchedule(schedule: ScheduleItem) {
  if (typeof Notification === 'undefined' || Notification.permission !== 'granted') {
    return;
  }

  const notification = new Notification(schedule.title, {
    body: createNotificationBody(schedule),
    tag: `schedule-${schedule.id}-${schedule.nextTriggerAt || schedule.scheduledFor}`,
  });

  notification.onclick = () => {
    window.focus();
    window.location.hash = '#schedule-form-card';
    notification.close();
  };
}

async function checkDueNotifications() {
  if (state.notificationPermission !== 'granted') return;

  const now = Date.now();
  const dueSchedules = state.schedules.filter((schedule) => {
    if (!schedule.nextTriggerAt) return false;
    const triggerAt = new Date(schedule.nextTriggerAt).getTime();
    const lastNotifiedAt = schedule.lastNotifiedAt ? new Date(schedule.lastNotifiedAt).getTime() : 0;

    return (
      !Number.isNaN(triggerAt) &&
      triggerAt <= now &&
      lastNotifiedAt < triggerAt &&
      !state.pendingAcks.has(schedule.id)
    );
  });

  for (const schedule of dueSchedules) {
    try {
      state.pendingAcks.add(schedule.id);
      notifySchedule(schedule);
      const nextSchedule = await acknowledgeSchedule(schedule.id);
      replaceSchedule(nextSchedule);
    } catch (error) {
      console.error(error);
    } finally {
      state.pendingAcks.delete(schedule.id);
    }
  }
}

async function requestNotificationPermission() {
  if (typeof Notification === 'undefined') {
    state.notificationPermission = 'unsupported';
    updateNotificationUI();
    return;
  }

  try {
    const permission = await Notification.requestPermission();
    state.notificationPermission = permission;
    updateNotificationUI();
    if (permission === 'granted') {
      recordAction('notification_permission_granted');
      setFeedback('浏览器提醒已开启，到点后会自动弹出通知。', 'success');
      await checkDueNotifications();
    }
  } catch (error) {
    console.error(error);
    setFeedback('提醒权限申请失败，请检查浏览器设置。', 'error');
  }
}

function startLoops() {
  if (state.fetchTimer) {
    clearInterval(state.fetchTimer);
  }
  if (state.notificationTimer) {
    clearInterval(state.notificationTimer);
  }

  state.fetchTimer = window.setInterval(() => {
    void refreshSchedules({ silent: true });
  }, POLL_INTERVAL);

  state.notificationTimer = window.setInterval(() => {
    void checkDueNotifications();
  }, NOTIFICATION_SCAN_INTERVAL);
}

document.addEventListener('click', (event) => {
  const target = event.target as HTMLElement | null;
  const actionButton = target?.closest<HTMLElement>('[data-action]');
  if (actionButton) {
    const action = actionButton.getAttribute('data-action');
    const scheduleId = Number(actionButton.getAttribute('data-id'));
    if (!action || Number.isNaN(scheduleId)) return;
    void handleAction(action, scheduleId);
    return;
  }

  if (target?.closest('#cancel-edit')) {
    resetForm();
    setFeedback('');
    return;
  }

  if (target?.closest('#refresh-schedules')) {
    void refreshSchedules();
    return;
  }

  if (target?.closest('#request-notification')) {
    void requestNotificationPermission();
    return;
  }

  if (target?.closest('#scroll-to-form')) {
    dom.formCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    dom.title.focus();
  }
});

dom.form.addEventListener('submit', (event) => {
  void handleSubmit(event as SubmitEvent);
});

document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    void refreshSchedules({ silent: true });
    void checkDueNotifications();
  }
});

window.addEventListener('beforeunload', () => {
  if (state.fetchTimer) clearInterval(state.fetchTimer);
  if (state.notificationTimer) clearInterval(state.notificationTimer);
});

setPageContext('schedule-board');
recordAction('schedule_board_loaded');
updateNotificationUI();
resetForm();
renderScheduleSections();
void refreshSchedules({ silent: true });
void checkDueNotifications();
startLoops();
