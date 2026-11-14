import { ApiErrorResponse, ApiResponseEnvelope } from "../types";

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;
  requestId?: string;

  constructor(status: number, code: string, message: string, details?: unknown, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.requestId = requestId;
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers: customHeaders, ...customOptions } = options;

  let url = endpoint.startsWith("http") ? endpoint : `${BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        searchParams.append(key, String(value));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const defaultHeaders: Record<string, string> = {
    Accept: "application/json",
  };

  if (!(customOptions.body instanceof FormData)) {
    defaultHeaders["Content-Type"] = "application/json";
  }

  const response = await fetch(url, {
    credentials: "include",
    headers: {
      ...defaultHeaders,
      ...((customHeaders as Record<string, string>) || {}),
    },
    ...customOptions,
  });

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  // Parse JSON response
  let json: unknown = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      json = await response.json();
    } catch {
      json = null;
    }
  }

  if (!response.ok) {
    if (json && typeof json === "object" && "error" in json) {
      const errRes = json as ApiErrorResponse;
      throw new ApiError(
        response.status,
        errRes.error.code || "API_ERROR",
        errRes.error.message || `Request failed with status ${response.status}`,
        errRes.error.details,
        errRes.error.request_id
      );
    }

    throw new ApiError(
      response.status,
      "HTTP_ERROR",
      `HTTP error ${response.status}: ${response.statusText}`,
      json
    );
  }

  // Unwrap {"data": ...} envelope if present
  if (json && typeof json === "object" && "data" in json) {
    return (json as ApiResponseEnvelope<T>).data;
  }

  return json as T;
}

export const apiClient = {
  get: <T>(url: string, params?: Record<string, string | number | boolean | undefined | null>) =>
    request<T>(url, { method: "GET", params }),

  post: <T>(url: string, body?: unknown) =>
    request<T>(url, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(url: string, body?: unknown) =>
    request<T>(url, {
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(url: string, body?: unknown) =>
    request<T>(url, {
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(url: string) =>
    request<T>(url, { method: "DELETE" }),

  // For raw streaming responses (e.g. CSV exports)
  getRaw: async (url: string, params?: Record<string, string | number | boolean | undefined | null>) => {
    let finalUrl = url.startsWith("http") ? url : `${BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") searchParams.append(k, String(v));
      });
      const q = searchParams.toString();
      if (q) finalUrl += (finalUrl.includes("?") ? "&" : "?") + q;
    }
    return fetch(finalUrl, {
      method: "GET",
      credentials: "include",
    });
  },

  // Uploading directly to presigned URL (S3 or local adapter)
  uploadToPresignedUrl: async (uploadUrl: string, file: Blob | File) => {
    const resp = await fetch(uploadUrl, {
      method: "PUT",
      body: file,
      headers: {
        "Content-Type": file.type || "text/csv",
      },
    });
    if (!resp.ok) {
      throw new Error(`File upload failed: ${resp.status} ${resp.statusText}`);
    }
    return resp;
  },
};
