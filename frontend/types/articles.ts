export type Article = {
  id: string;
  title: string;
  content: string | null;
  summary: string | null;
  source_url: string | null;
  source_type: string | null;
  category: string | null;
  importance_score: number | null;
  metadata?: Record<string, unknown> | null;
  collected_at: string;
  vector_id?: string | null;
};

export type ArticleListResponse = {
  articles: Article[];
  total: number;
  skip: number;
  limit: number;
};

export type ArticleSearchResult = Article & {
  similarity_score?: number | null;
  article_metadata?: Record<string, unknown> | null;
  published_at?: string | null;
};

export type ArticleSearchResponse = {
  query: string;
  results: ArticleSearchResult[];
  total: number;
};

export type ArticleStatisticsResponse = {
  total: number;
  by_source_type: Record<string, number>;
  by_category: Record<string, number>;
  average_importance_score: number;
};
