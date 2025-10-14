/**
 * Represents an error returned from an API call.
 *
 * @property message - Human-readable error message
 * @property status - HTTP status code associated with the error
 */
export interface ApiError {
  message: string;
  status: number;
}

/**
 * Generic wrapper for API responses.
 *
 * @template T - The type of the successful response data
 * @property data - The actual response payload
 * @property error - Optional error information if the request failed
 */
export interface ApiResponse<T> {
  data: T;
  error?: ApiError;
}