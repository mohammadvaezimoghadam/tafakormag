export type ProposalStatus = 'pending' | 'approved' | 'rejected'

export interface EditorialUser {
  id: string | number
  name: string
  avatar?: string
  role?: 'creator' | 'admin' | 'editor' | 'member' | string
}

export interface PostEditProposal {
  id: string
  postId: string | number
  topicId?: string | number
  postTitle?: string
  editor: EditorialUser
  originalContent: string
  proposedContent: string
  original_content?: string
  proposed_content?: string
  proposedMediaUrls?: string[]
  originalMediaUrls?: string[]
  status: ProposalStatus
  createdAt: string
  reason?: string
  reviewedBy?: EditorialUser | null
  reviewedAt?: string | null
  reviewNote?: string | null
}

export interface PostEditHistoryItem {
  id: string
  proposalId?: string
  postId: string | number
  editor: EditorialUser
  approvedBy?: EditorialUser
  approver?: EditorialUser
  appliedAt?: string
  createdAt?: string
  previousContent?: string
  newContent?: string
  content?: string
  note?: string
  summaryOfChanges?: string
}
