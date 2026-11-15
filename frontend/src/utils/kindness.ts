import type { CampaignCategory, CampaignStatus, DonationCampaignProps } from '@/types/kindness'

const CATEGORY_LABELS: Record<string, { fa: string; en: string }> = {
  mosque: { fa: 'مسجد و اماکن مذهبی', en: 'Mosque & Religious' },
  school: { fa: 'مدرسه و آموزش', en: 'School & Education' },
  education: { fa: 'آموزش و تحصیلی', en: 'Education' },
  health: { fa: 'درمانی و سلامت', en: 'Health & Medical' },
  treatment: { fa: 'درمانی و سلامت', en: 'Medical Care' },
  livelihood: { fa: 'نیازمندان و معیشت', en: 'Livelihood & Aid' },
  living: { fa: 'معیشتی و نیازمندان', en: 'Living Support' },
  construction: { fa: 'عمرانی و تجهیزات', en: 'Construction & Equipment' },
  freedom: { fa: 'آزادی زندانیان', en: 'Prisoner Aid' },
  dowry: { fa: 'تهیه جهیزیه', en: 'Dowry Support' },
  employment: { fa: 'اشتغال و کارآفرینی', en: 'Employment' },
  general: { fa: 'عمومی و متفرقه', en: 'Community' },
  other: { fa: 'متفرقه و عمومی', en: 'Other' },
}

export function normalizeCampaignCategory(category?: string | null): CampaignCategory {
  const cat = (category || '').trim().toLowerCase()
  if (cat === 'mosque' || cat.includes('mosque') || cat.includes('مسجد') || cat.includes('مذهبی')) {
    return 'mosque'
  }
  if (
    cat === 'school' ||
    cat === 'education' ||
    cat.includes('school') ||
    cat.includes('مدرسه') ||
    cat.includes('آموزش')
  ) {
    return 'school'
  }
  if (
    cat === 'health' ||
    cat === 'treatment' ||
    cat.includes('health') ||
    cat.includes('درمان') ||
    cat.includes('سلامت')
  ) {
    return 'health'
  }
  if (
    cat === 'livelihood' ||
    cat === 'living' ||
    cat.includes('livelihood') ||
    cat.includes('نیازمند') ||
    cat.includes('معیشت')
  ) {
    return 'livelihood'
  }
  if (
    cat === 'construction' ||
    cat.includes('construction') ||
    cat.includes('عمران') ||
    cat.includes('تجهیز')
  ) {
    return 'construction'
  }
  return 'other'
}

export function getCampaignCategoryLabel(category?: string | null, isFa = true): string {
  const raw = (category || '').trim()
  if (!raw) {
    return isFa ? 'عمومی و متفرقه' : 'Community'
  }
  const key = raw.toLowerCase()
  const direct = CATEGORY_LABELS[key]
  if (direct) {
    return isFa ? direct.fa : direct.en
  }
  // If raw string is already non-ASCII (e.g. Persian custom category), keep it in FA mode
  const normalized = normalizeCampaignCategory(raw)
  const fallbackLabel = CATEGORY_LABELS[normalized] ?? {
    fa: 'متفرقه و عمومی',
    en: 'Other',
  }
  if (/[^\x00-\x7F]/.test(raw)) {
    return isFa ? raw : fallbackLabel.en
  }
  return isFa ? fallbackLabel.fa : fallbackLabel.en
}

export function getCampaignStatusConfig(status?: string | null, isFa = true) {
  switch (status) {
    case 'pending_review':
      return {
        label: isFa ? 'در انتظار تأیید' : 'Pending Review',
        variant: 'secondary' as const,
        isCompleted: false,
        isInactive: true,
      }
    case 'completed':
      return {
        label: isFa ? 'تکمیل شده' : 'Completed',
        variant: 'outline' as const,
        isCompleted: true,
        isInactive: false,
      }
    case 'executed':
      return {
        label: isFa ? 'اجرا شده و شفاف' : 'Executed',
        variant: 'default' as const,
        isCompleted: true,
        isInactive: false,
      }
    case 'expired':
      return {
        label: isFa ? 'پایان‌یافته' : 'Expired',
        variant: 'outline' as const,
        isCompleted: false,
        isInactive: true,
      }
    case 'paused':
      return {
        label: isFa ? 'در حال بررسی' : 'Paused',
        variant: 'secondary' as const,
        isCompleted: false,
        isInactive: true,
      }
    case 'inactive':
      return {
        label: isFa ? 'متوقف / غیرفعال' : 'Inactive',
        variant: 'destructive' as const,
        isCompleted: false,
        isInactive: true,
      }
    case 'active':
    default:
      return {
        label: isFa ? 'در حال جمع‌آوری' : 'Active',
        variant: 'secondary' as const,
        isCompleted: false,
        isInactive: false,
      }
  }
}

export function formatKindnessNumber(val: number | string | null | undefined, isFa = true): string {
  const num = Number(val ?? 0)
  if (!Number.isFinite(num)) return isFa ? '۰' : '0'
  return new Intl.NumberFormat(isFa ? 'fa-IR' : 'en-US').format(num)
}

export function resolveKindnessMediaUrl(raw?: string | null): string | null {
  if (!raw) return null
  if (raw.startsWith('http://') || raw.startsWith('https://') || raw.startsWith('/')) {
    return raw
  }
  return `/${raw}`
}

function getFileBasename(url: string): string {
  try {
    const clean = url.split('?')[0] || url
    const parts = clean.split('/')
    return (parts[parts.length - 1] || clean).toLowerCase()
  } catch {
    return url.toLowerCase()
  }
}

export function extractCampaignMediaGallery(item: any): string[] {
  const candidates: string[] = []
  const coverUrl = resolveKindnessMediaUrl(item?.cover_image)
  if (coverUrl) {
    candidates.push(coverUrl)
  }
  if (Array.isArray(item?.attachments)) {
    for (const att of item.attachments) {
      if (att && !att.is_video && att.url) {
        const resolved = resolveKindnessMediaUrl(att.url)
        if (resolved) {
          candidates.push(resolved)
        }
      }
    }
  }

  // Deduplicate exact URLs and cover/attachment copies of the same uploaded filename
  const seenNames = new Set<string>()
  const unique: string[] = []
  for (const url of candidates) {
    const key = getFileBasename(url)
    if (!seenNames.has(key)) {
      seenNames.add(key)
      unique.push(url)
    }
  }
  return unique
}

export function getCampaignDaysRemaining(deadline?: string | null): number | null {
  if (!deadline) return null
  const targetMs = new Date(deadline).getTime()
  if (!Number.isFinite(targetMs)) return null
  const diffDays = Math.ceil((targetMs - Date.now()) / (1000 * 60 * 60 * 24))
  return Math.max(0, diffDays)
}

export function mapApiCampaignToProps(
  item: any,
  currentUserId: string | null,
  currentUserPhone: string | null,
  isFa = true
): DonationCampaignProps {
  const creatorId = item.creator_info?.id || item.creator?.id || item.creator
  const creatorPhone = item.creator_info?.phone || item.creator?.phone
  const canEdit = Boolean(
    (currentUserId && creatorId && String(creatorId) === currentUserId) ||
      (currentUserPhone && creatorPhone && creatorPhone === currentUserPhone)
  )

  const locale = isFa ? 'fa-IR' : 'en-US'
  const topicId = typeof item.topic === 'object' ? item.topic?.id : item.topic
  const topicName =
    item.topic_title ||
    (typeof item.topic === 'object' ? item.topic?.name || item.topic?.title : null) ||
    (isFa ? 'تاپیک عمومی' : 'General Topic')

  return {
    id: item.id,
    title: item.title,
    description: item.description || '',
    topicId: topicId ?? 1,
    topicName,
    category: item.category || 'mosque',
    status: (item.status || 'active') as CampaignStatus,
    targetAmount: Number(item.target_amount) || 0,
    collectedAmount: Number(item.collected_amount) || 0,
    donorsCount: Number(item.donors_count) || item.donors?.length || 0,
    authorName:
      item.creator_info?.name ||
      item.creator?.first_name ||
      (isFa ? 'مدیر پویش' : 'Organizer'),
    authorAvatar: resolveKindnessMediaUrl(item.creator_info?.avatar) || undefined,
    creatorId,
    creatorPhone,
    canEdit,
    timestamp: item.created_at
      ? new Date(item.created_at).toLocaleDateString(locale)
      : isFa
        ? 'هم‌اکنون'
        : 'Just now',
    deadline: item.deadline || null,
    iban: item.iban || null,
    mediaGallery: extractCampaignMediaGallery(item),
    recentDonors: (item.donors || []).map((d: any) => ({
      id: String(d.id),
      name:
        d.name ||
        (d.is_anonymous
          ? isFa
            ? 'کاربر ناشناس'
            : 'Anonymous'
          : isFa
            ? 'حامی گرامی'
            : 'Supporter'),
      amount: Number(d.amount) || 0,
      avatarUrl: resolveKindnessMediaUrl(d.avatar) || undefined,
      isAnonymous: Boolean(d.is_anonymous),
      donatedAt: d.donated_at
        ? new Date(d.donated_at).toLocaleDateString(locale)
        : isFa
          ? 'به‌تازگی'
          : 'Recently',
    })),
    transparency:
      item.transparency_logs?.length > 0
        ? {
            isAvailable: true,
            executedAt: item.transparency_logs[0]?.date
              ? new Date(item.transparency_logs[0].date).toLocaleDateString(locale)
              : undefined,
            description:
              item.transparency_logs[0]?.description ||
              item.transparency_logs[0]?.title ||
              '',
            receiptImages: item.transparency_logs
              .map((l: any) => resolveKindnessMediaUrl(l.receipt_url))
              .filter(Boolean),
            costBreakdown: item.transparency_logs.reduce((acc: Record<string, number>, curr: any) => {
              acc[curr.title] = Number(curr.amount) || 0
              return acc
            }, {}),
          }
        : undefined,
    availablePayoutBalance: Number(item.available_payout_balance) || 0,
    totalSettledAmount: Number(item.total_settled_amount) || 0,
    canRequestPayout: Boolean(item.can_request_payout),
    isEnded: Boolean(item.is_ended),
  }
}

