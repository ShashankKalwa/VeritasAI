import { supabase } from './supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Analyze an article/headline for fake news via backend API
 * Uses ensemble ML model + heuristic engine on the server
 */
export async function analyzeArticle(text) {
  if (!text || text.trim().length < 10) {
    throw new Error('Text must be at least 10 characters long');
  }

  const cleanText = text.replace(/<[^>]*>/g, '').trim();
  if (cleanText.length > 5000) {
    throw new Error('Text must be under 5000 characters');
  }

  const response = await fetch(`${API_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: cleanText }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || 'Analysis failed. Please try again.');
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
 * Get recent analyses for feed from backend
 */
export async function getRecentAnalyses(limit = 10) {
  const response = await fetch(`${API_URL}/api/feed?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch feed');
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
