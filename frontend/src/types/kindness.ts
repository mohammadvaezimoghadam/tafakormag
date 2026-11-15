export type CampaignStatus = 'pending_review' | 'active' | 'completed' | 'executed' | 'expired' | 'paused' | 'inactive';

export type CampaignCategory = 'mosque' | 'school' | 'health' | 'livelihood' | 'construction' | 'other';

export interface Donor {
  id: string;
  name: string;
  amount: number;
  avatarUrl?: string;
  isAnonymous: boolean;
  donatedAt: string;
}

export interface TransparencyReport {
  isAvailable: boolean;
  executedAt?: string;
  description: string;
  receiptImages: string[];
  costBreakdown: Record<string, number>; // e.g., { "Material Purchase": 15000000, "Transport": 1000000 }
}

export interface DonationCampaignProps {
  id: string | number;
  title: string;
  description: string;
  topicId: string | number;
  topicName: string;
  category: string;
  status: CampaignStatus;
  targetAmount: number;
  collectedAmount: number;
  donorsCount: number;
  recentDonors: Donor[];
  mediaGallery: string[];
  transparency?: TransparencyReport;
  authorName?: string;
  authorAvatar?: string;
  creatorId?: string | number;
  creatorPhone?: string;
  canEdit?: boolean;
  timestamp?: string;
  deadline?: string | null;
  iban?: string | null;
  availablePayoutBalance?: number;
  totalSettledAmount?: number;
  canRequestPayout?: boolean;
  isEnded?: boolean;
  isEmbedded?: boolean;
}

export interface PayoutRequestItem {
  id: string;
  campaign: string;
  campaign_title: string;
  amount: number;
  iban: string;
  account_holder_name: string;
  status: 'pending' | 'approved' | 'completed' | 'rejected';
  status_display: string;
  tracking_number?: string;
  receipt_url?: string;
  rejection_reason?: string;
  admin_notes?: string;
  settled_at?: string;
  created_at: string;
}

export interface CreateDonationMediaFile {
  id: string;
  file: File;
  previewUrl: string;
  isVideo: boolean;
}

export interface CreateDonationFormState {
  title: string;
  category: CampaignCategory;
  targetAmount: number | null; // Raw numeric amount in Tomans
  description: string;
  mediaFiles: CreateDonationMediaFile[];
  autoPin: boolean;
  deadline?: string | null;
}

export interface CreateDonationPayload {
  topic_id: string | number;
  title: string;
  category: CampaignCategory;
  target_amount: number;
  description: string;
  media_files: File[];
  auto_pin: boolean;
  deadline?: string | null;
}
