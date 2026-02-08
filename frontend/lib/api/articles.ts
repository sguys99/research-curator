import apiClient from "@/lib/api/client";
import type {
  ArticleListResponse,
  ArticleSearchResponse,
  ArticleStatisticsResponse,
} from "@/types/articles";

export type ArticleFilters = {
  source_type?: string[];
  category?: string[];
  min_importance_score?: number;
  date_from?: string;
  date_to?: string;
};

export const getArticles = async (
  params: {
    skip?: number;
    limit?: number;
  } & ArticleFilters,
): Promise<ArticleListResponse> => {
  const response = await apiClient.get<ArticleListResponse>("/api/articles", { params });
  return response.data;
};

export const getArticleStatistics = async (): Promise<ArticleStatisticsResponse> => {
  const response = await apiClient.get<ArticleStatisticsResponse>("/api/articles/statistics/summary");
  return response.data;
};

export const searchSemantic = async (payload: {
  query: string;
  limit?: number;
  score_threshold?: number;
} & ArticleFilters): Promise<ArticleSearchResponse> => {
  const response = await apiClient.post<ArticleSearchResponse>("/api/articles/search", payload);
  return response.data;
};

export const searchKeyword = async (
  query: string,
  params?: { skip?: number; limit?: number },
): Promise<ArticleListResponse> => {
  const response = await apiClient.get<ArticleListResponse>("/api/articles/keyword-search", {
    params: { q: query, ...params },
  });
  return response.data;
};

export const getSimilarArticles = async (articleId: string): Promise<ArticleSearchResponse> => {
  const response = await apiClient.get<ArticleSearchResponse>(`/api/articles/${articleId}/similar`);
  return response.data;
};
