import apiClient from "@/lib/api/client";

export type MagicLinkResponse = {
  message: string;
  token?: string | null;
};

export type VerifyResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string | null;
    created_at?: string;
    last_login?: string;
  };
};

export const requestMagicLink = async (email: string): Promise<MagicLinkResponse> => {
  const response = await apiClient.post<MagicLinkResponse>("/auth/magic-link", { email });
  return response.data;
};

export const verifyMagicLink = async (token: string): Promise<VerifyResponse> => {
  const response = await apiClient.get<VerifyResponse>("/auth/verify", { params: { token } });
  return response.data;
};
