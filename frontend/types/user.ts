export type User = {
  id: string;
  email: string;
  name: string | null;
  created_at?: string;
  last_login?: string;
};

export type UserPreferences = {
  research_fields: string[];
  keywords: string[];
  sources: string[];
  info_types: {
    paper: number;
    news: number;
    report: number;
  };
  email_time: string;
  daily_limit: number;
  email_enabled: boolean;
};
