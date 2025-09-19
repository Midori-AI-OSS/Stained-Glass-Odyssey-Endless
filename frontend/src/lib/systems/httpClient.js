// Shared HTTP client utility for frontend-backend communication
// Eliminates duplication between api.js and uiApi.js

import { openOverlay } from './OverlayController.js';
import { getApiBase } from './backendDiscovery.js';

// Cached API base to avoid repeated discovery calls
let cachedApiBase = null;

/**
 * Ensure we have a valid API base URL
 * @returns {Promise<string>} The API base URL
 */
async function ensureApiBase() {
  if (!cachedApiBase) {
    cachedApiBase = await getApiBase();
  }
  return cachedApiBase;
}

/**
 * Reset the cached API base (useful for testing or when backend changes)
 */
export function resetApiBase() {
  cachedApiBase = null;
}

/**
 * Standard error response structure
 * @typedef {Object} ErrorResponse
 * @property {string} message - Human readable error message
 * @property {string} [traceback] - Stack trace for debugging
 * @property {number} [status] - HTTP status code
 * @property {string} [code] - Error code for programmatic handling
 */

/**
 * Normalize error messages from various sources
 * @param {any} error - Error from various sources (Response, Error, string, etc.)
 * @param {Response} [response] - Original fetch response
 * @param {string} [context] - Additional context for the error
 * @returns {ErrorResponse} Normalized error object
 */
function normalizeError(error, response = null, context = '') {
  let message = '';
  let traceback = '';
  let status = response?.status || 0;

  // Try to extract error data from response
  if (response && !response.ok) {
    try {
      // If error is already parsed JSON data
      if (error && typeof error === 'object' && !error.message) {
        message = error.error || error.message || '';
        traceback = error.traceback || '';
      }
    } catch {}
  }

  // Extract from Error objects
  if (error instanceof Error) {
    message = error.message || '';
    traceback = error.stack || '';
  }

  // Handle string errors
  if (typeof error === 'string') {
    message = error;
  }

  // Fallback message
  if (!message) {
    message = response ? `HTTP error ${response.status}` : 'Unknown error';
  }

  // Normalize bare numeric error codes to descriptive messages
  const trimmed = String(message).trim();
  if (/^\d+$/.test(trimmed)) {
    message = `Unexpected error (code ${trimmed})${context ? ` during ${context}` : ''}`;
  }

  return {
    message: message.trim(),
    traceback: traceback.trim(),
    status,
    code: response ? `HTTP_${response.status}` : 'UNKNOWN'
  };
}

/**
 * Enhanced fetch with consistent error handling, URL construction, and logging
 * @param {string} url - Relative or absolute URL
 * @param {RequestInit} [options={}] - Fetch options
 * @param {Function} [parser] - Custom response parser function (default: response.json())
 * @param {boolean} [suppressOverlay=false] - Skip showing error overlay
 * @returns {Promise<any>} Parsed response data
 */
export async function httpRequest(url, options = {}, parser = null, suppressOverlay = false) {
  // Ensure we have the API base before making the request
  const apiBase = await ensureApiBase();
  
  // Construct full URL - handle both relative and absolute URLs
  const fullUrl = url.startsWith('http') 
    ? url 
    : `${apiBase}${url.startsWith('/') ? '' : '/'}${url}`;

  // Default parser
  if (!parser) {
    parser = async (response) => response.json();
  }

  const method = options.method || 'GET';
  const context = `${method} ${url}`;

  try {
    // Make the request
    const response = await fetch(fullUrl, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    // Handle non-ok responses
    if (!response.ok) {
      let errorData = null;
      
      // Try to parse error response as JSON
      try {
        const text = await response.text();
        if (text.trim()) {
          try {
            errorData = JSON.parse(text);
          } catch {
            errorData = { message: text };
          }
        }
      } catch {}

      const normalizedError = normalizeError(errorData, response, context);
      
      // Show error overlay for most errors (except 404s which callers often handle)
      const fatalBackendError = response.status >= 500 && Boolean(normalizedError.traceback);

      if (!suppressOverlay && response.status !== 404) {
        const overlayType = fatalBackendError ? 'backend-shutdown' : 'error';
        const overlayPayload = fatalBackendError
          ? { ...normalizedError, status: response.status }
          : normalizedError;
        openOverlay(overlayType, overlayPayload);
        console.error('HTTP Error:', { url: fullUrl, fatalBackendError, ...normalizedError });
      }

      const error = new Error(normalizedError.message);
      error.status = normalizedError.status;
      error.code = normalizedError.code;
      error.traceback = normalizedError.traceback;
      error.overlayShown = !suppressOverlay && response.status !== 404;
      throw error;
    }

    // Parse successful response
    return await parser(response);

  } catch (error) {
    // Handle network errors and other exceptions
    if (!error.overlayShown && !suppressOverlay) {
      const normalizedError = normalizeError(error, null, context);
      openOverlay('error', normalizedError);
      console.error('Network Error:', { url: fullUrl, ...normalizedError });
    }
    throw error;
  }
}

/**
 * Convenience method for GET requests
 * @param {string} url - URL to request
 * @param {RequestInit} [options={}] - Additional fetch options
 * @param {boolean} [suppressOverlay=false] - Skip error overlay
 * @returns {Promise<any>} Response data
 */
export async function httpGet(url, options = {}, suppressOverlay = false) {
  return httpRequest(url, { ...options, method: 'GET' }, null, suppressOverlay);
}

/**
 * Convenience method for POST requests with JSON body
 * @param {string} url - URL to request
 * @param {any} [data={}] - Data to send as JSON body
 * @param {RequestInit} [options={}] - Additional fetch options
 * @param {boolean} [suppressOverlay=false] - Skip error overlay
 * @returns {Promise<any>} Response data
 */
export async function httpPost(url, data = {}, options = {}, suppressOverlay = false) {
  return httpRequest(url, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data)
  }, null, suppressOverlay);
}

/**
 * Convenience method for PUT requests with JSON body
 * @param {string} url - URL to request
 * @param {any} [data={}] - Data to send as JSON body
 * @param {RequestInit} [options={}] - Additional fetch options
 * @param {boolean} [suppressOverlay=false] - Skip error overlay
 * @returns {Promise<any>} Response data
 */
export async function httpPut(url, data = {}, options = {}, suppressOverlay = false) {
  return httpRequest(url, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data)
  }, null, suppressOverlay);
}

/**
 * Convenience method for DELETE requests
 * @param {string} url - URL to request
 * @param {RequestInit} [options={}] - Additional fetch options
 * @param {boolean} [suppressOverlay=false] - Skip error overlay
 * @returns {Promise<any>} Response data
 */
export async function httpDelete(url, options = {}, suppressOverlay = false) {
  return httpRequest(url, { ...options, method: 'DELETE' }, null, suppressOverlay);
}

/**
 * Special method for binary/blob responses
 * @param {string} url - URL to request
 * @param {RequestInit} [options={}] - Additional fetch options
 * @param {boolean} [suppressOverlay=false] - Skip error overlay
 * @returns {Promise<Blob>} Response as blob
 */
export async function httpBlob(url, options = {}, suppressOverlay = false) {
  return httpRequest(url, options, (response) => response.blob(), suppressOverlay);
}

/**
 * Method for requests that return boolean success (e.g., DELETE operations)
 * @param {string} url - URL to request
 * @param {RequestInit} [options={}] - Additional fetch options
 * @param {boolean} [suppressOverlay=false] - Skip error overlay
 * @returns {Promise<boolean>} True if request was successful
 */
export async function httpSuccess(url, options = {}, suppressOverlay = false) {
  return httpRequest(url, options, (response) => response.ok, suppressOverlay);
}