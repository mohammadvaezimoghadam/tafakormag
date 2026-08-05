export type CampaignStatus = 'active' | 'completed' | 'executed';

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
}
