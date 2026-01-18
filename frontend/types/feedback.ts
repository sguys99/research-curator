export type Feedback = {
  id: string;
  user_id: string;
  article_id: string;
  rating: number;
  comment?: string | null;
  created_at: string;
};

export type FeedbackCreatePayload = {
  article_id: string;
  rating: number;
  comment?: string | null;
};

export type FeedbackUpdatePayload = {
  rating?: number;
  comment?: string | null;
};

export type FeedbackListResponse = {
  feedback: Feedback[];
  total: number;
  skip: number;
  limit: number;
};

export type FeedbackStatsResponse = {
  article_id: string;
  count: number;
  average_rating: number;
  rating_distribution: Record<string, number>;
};
