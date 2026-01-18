"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import {
  getArticles,
  getArticleStatistics,
  getSimilarArticles,
  searchKeyword,
  searchSemantic,
} from "@/lib/api/articles";
import type { ArticleSearchResult } from "@/types/articles";

const sourceTypeOptions = ["paper", "news", "report"];

type SearchMode = "semantic" | "keyword";

type SearchResult = {
  id: string;
  title: string;
  summary: string;
  source_url: string | null;
  source_type: string | null;
  category: string | null;
  importance_score: number | null;
  similarity_score?: number | null;
};

const normalizeResults = (results: ArticleSearchResult[]): SearchResult[] =>
  results.map((item) => ({
    id: item.id,
    title: item.title,
    summary: item.summary ?? item.content ?? "Summary unavailable.",
    source_url: item.source_url ?? null,
    source_type: item.source_type ?? null,
    category: item.category ?? null,
    importance_score: item.importance_score ?? null,
    similarity_score: item.similarity_score ?? null,
  }));

const formatScore = (value?: number | null) =>
  value === null || value === undefined ? "-" : value.toFixed(2);

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("semantic");
  const [sourceTypes, setSourceTypes] = useState<string[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [minImportance, setMinImportance] = useState("0.7");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [similarResults, setSimilarResults] = useState<SearchResult[]>([]);
  const [similarTitle, setSimilarTitle] = useState<string | null>(null);

  const statsQuery = useQuery({
    queryKey: ["articles", "stats"],
    queryFn: getArticleStatistics,
  });

  const recentQuery = useQuery({
    queryKey: ["articles", "recent"],
    queryFn: () => getArticles({ limit: 8 }),
  });

  const semanticMutation = useMutation({
    mutationFn: searchSemantic,
    onSuccess: (data) => {
      setResults(normalizeResults(data.results));
      setHasSearched(true);
    },
  });

  const keywordMutation = useMutation({
    mutationFn: (value: string) => searchKeyword(value, { limit: 20 }),
    onSuccess: (data) => {
      const normalized = data.articles.map((item) => ({
        id: item.id,
        title: item.title,
        summary: item.summary ?? item.content ?? "Summary unavailable.",
        source_url: item.source_url ?? null,
        source_type: item.source_type ?? null,
        category: item.category ?? null,
        importance_score: item.importance_score ?? null,
      }));
      setResults(normalized);
      setHasSearched(true);
    },
  });

  const similarMutation = useMutation({
    mutationFn: getSimilarArticles,
    onSuccess: (data) => {
      setSimilarResults(normalizeResults(data.results));
      setSimilarTitle(data.query);
    },
  });

  const categoryOptions = useMemo(() => {
    const stats = statsQuery.data?.by_category ?? {};
    return Object.keys(stats).sort();
  }, [statsQuery.data]);

  const isSearching = semanticMutation.isPending || keywordMutation.isPending;

  const handleSearch = () => {
    if (!query.trim()) {
      return;
    }
    setSimilarResults([]);
    setSimilarTitle(null);

    if (mode === "semantic") {
      semanticMutation.mutate({
        query,
        limit: 20,
        score_threshold: 0.7,
        source_type: sourceTypes.length ? sourceTypes : undefined,
        category: categories.length ? categories : undefined,
        min_importance_score: minImportance ? Number(minImportance) : undefined,
        date_from: dateFrom ? new Date(dateFrom).toISOString() : undefined,
        date_to: dateTo ? new Date(dateTo).toISOString() : undefined,
      });
    } else {
      keywordMutation.mutate(query);
    }
  };

  const toggleValue = (value: string, list: string[], setter: (next: string[]) => void) => {
    if (list.includes(value)) {
      setter(list.filter((item) => item !== value));
    } else {
      setter([...list, value]);
    }
  };

  const fallbackResults: SearchResult[] =
    !hasSearched && recentQuery.data
      ? recentQuery.data.articles.map((item) => ({
          id: item.id,
          title: item.title,
          summary: item.summary ?? item.content ?? "Summary unavailable.",
          source_url: item.source_url ?? null,
          source_type: item.source_type ?? null,
          category: item.category ?? null,
          importance_score: item.importance_score ?? null,
        }))
      : [];

  const displayResults = hasSearched ? results : fallbackResults;

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="font-display text-xl font-semibold text-slate-900">Search</h2>
            <p className="mt-2 text-sm text-slate-500">
              Run semantic or keyword searches across the curated archive.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full bg-slate-100 p-1 text-xs font-medium text-slate-600">
            {(["semantic", "keyword"] as const).map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => setMode(option)}
                className={`rounded-full px-4 py-2 transition-colors ${
                  mode === option ? "bg-white text-slate-900 shadow-sm" : "hover:text-slate-900"
                }`}
              >
                {option === "semantic" ? "Semantic" : "Keyword"}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 md:flex-row">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search papers, keywords, or authors"
            className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm text-slate-700 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
          <button
            type="button"
            onClick={handleSearch}
            className="rounded-full bg-blue-600 px-6 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-300"
            disabled={isSearching}
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_1fr_1fr]">
          <div>
            <p className="text-xs font-semibold text-slate-500">Source type</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {sourceTypeOptions.map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => toggleValue(type, sourceTypes, setSourceTypes)}
                  className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                    sourceTypes.includes(type)
                      ? "border-blue-200 bg-blue-50 text-blue-700"
                      : "border-slate-200 bg-slate-50 text-slate-600"
                  }`}
                  disabled={mode === "keyword"}
                >
                  {type}
                </button>
              ))}
            </div>
            {mode === "keyword" ? (
              <p className="mt-2 text-[11px] text-slate-400">Filters apply to semantic search.</p>
            ) : null}
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-500">Category</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {categoryOptions.length ? (
                categoryOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => toggleValue(option, categories, setCategories)}
                    className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                      categories.includes(option)
                        ? "border-blue-200 bg-blue-50 text-blue-700"
                        : "border-slate-200 bg-slate-50 text-slate-600"
                    }`}
                    disabled={mode === "keyword"}
                  >
                    {option}
                  </button>
                ))
              ) : (
                <span className="text-xs text-slate-400">No category stats yet</span>
              )}
            </div>
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-500">Importance threshold</p>
            <select
              value={minImportance}
              onChange={(event) => setMinImportance(event.target.value)}
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-600"
              disabled={mode === "keyword"}
            >
              <option value="0.9">0.90+ high priority</option>
              <option value="0.8">0.80+ curated</option>
              <option value="0.7">0.70+ default</option>
              <option value="0.5">0.50+ broad</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex flex-col gap-3 text-xs text-slate-500 md:flex-row md:items-center">
          <div className="flex items-center gap-2">
            <span>From</span>
            <input
              type="date"
              value={dateFrom}
              onChange={(event) => setDateFrom(event.target.value)}
              className="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600"
              disabled={mode === "keyword"}
            />
          </div>
          <div className="flex items-center gap-2">
            <span>To</span>
            <input
              type="date"
              value={dateTo}
              onChange={(event) => setDateTo(event.target.value)}
              className="rounded-lg border border-slate-200 px-2 py-1 text-xs text-slate-600"
              disabled={mode === "keyword"}
            />
          </div>
        </div>
      </div>

      {similarResults.length ? (
        <div className="rounded-2xl border border-blue-100 bg-blue-50 p-6 text-sm text-blue-700">
          <p className="font-semibold">{similarTitle ?? "Similar articles"}</p>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {similarResults.map((result) => (
              <div key={result.id} className="rounded-2xl border border-blue-100 bg-white p-4">
                <p className="text-sm font-semibold text-slate-900">{result.title}</p>
                <p className="mt-2 text-xs text-slate-600 max-h-16 overflow-hidden">{result.summary}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {displayResults.map((result) => (
          <div key={result.id} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between gap-4">
              <p className="text-sm font-semibold text-slate-900">{result.title}</p>
              <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] text-slate-500">
                Score {formatScore(result.similarity_score ?? result.importance_score)}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-600 max-h-16 overflow-hidden">{result.summary}</p>
            <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
              <span>
                {result.source_type ?? "unknown"}
                {result.category ? ` • ${result.category}` : ""}
              </span>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => similarMutation.mutate(result.id)}
                  className="font-medium text-blue-600"
                >
                  Find similar
                </button>
                {result.source_url ? (
                  <a
                    href={result.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-slate-600"
                  >
                    Open source
                  </a>
                ) : null}
              </div>
            </div>
          </div>
        ))}
      </div>

      {!displayResults.length ? (
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-500">
          No results yet. Try a broader query or collect more articles.
        </div>
      ) : null}
    </div>
  );
}
