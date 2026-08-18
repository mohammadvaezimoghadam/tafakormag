export type CampaignStatus = 'active' | 'completed' | 'executed' | 'inactive';

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
  isEmbedded?: boolean;
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
