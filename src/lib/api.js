import { supabase } from './supabase';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Analyze text/URL for misinformation via v2 pipeline
 * Sends input_type and content_type for the new claim-level analysis
 */
export async function analyzeArticle(text, inputType = 'text', contentType = 'auto') {
  if (!text || text.trim().length < 10) {
    throw new Error('Text must be at least 10 characters long');
  }

  const cleanText = text.replace(/<[^>]*>/g, '').trim();
  if (cleanText.length > 10000) {
    throw new Error('Text must be under 10000 characters');
  }

  const response = await fetch(`${API_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: cleanText,
      input_type: inputType,
      content_type: contentType,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis failed. Please try again.');
  }

  return await response.json();
}

/**
 * Analyze a file upload
 */
export async function analyzeFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_URL}/api/analyze/file`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'File analysis failed');
  }

  return await response.json();
}

/**
 * Get dashboard statistics from backend
 */
export async function getStats() {
  const response = await fetch(`${API_URL}/api/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return await response.json();
}

/**
 * Get recent analyses for the live feed
 */
export async function getLiveFeed(limit = 20, offset = 0, source = 'all', verdict = '') {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
    source: source,
  });
  if (verdict) params.set('verdict', verdict);

  const response = await fetch(`${API_URL}/api/feed?${params}`);
  if (!response.ok) throw new Error('Failed to fetch live feed');
  const result = await response.json();
  return result.data;
}

/**
 * Get trending claims
 */
export async function getTrendingClaims(limit = 20, offset = 0, verdict = '') {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  if (verdict) params.set('verdict', verdict);

  const response = await fetch(`${API_URL}/api/trending?${params}`);
  if (!response.ok) throw new Error('Failed to fetch trending claims');
  const result = await response.json();
  return result.data;
}


/**
 * Get dataset with filtering from backend
 */
export async function getDataset({ label, category, search, page = 1, pageSize = 20 }) {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });
  if (label && label !== 'all') params.set('label', label);
  if (category && category !== 'All') params.set('category', category);
  if (search) params.set('search', search);

  const response = await fetch(`${API_URL}/api/dataset?${params}`);
  if (!response.ok) throw new Error('Failed to fetch dataset');
  return await response.json();
}

/**
 * Get dataset stats from backend
 */
export async function getDatasetStats() {
  const response = await fetch(`${API_URL}/api/dataset/stats`);
  if (!response.ok) throw new Error('Failed to fetch dataset stats');
  return await response.json();
}
