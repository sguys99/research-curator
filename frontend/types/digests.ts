export type Digest = {
  id: string;
  user_id: string;
  article_ids: string[];
  sent_at: string;
  email_opened: boolean;
  opened_at: string | null;
};

export type DigestListResponse = {
  digests: Digest[];
  total: number;
};
