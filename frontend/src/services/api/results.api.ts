export function getResultDownloadUrl(filename: string): string {
  const rawBaseUrl = process.env.NEXT_PUBLIC_BACKEND1_URL || 'http://localhost:3001';
  const cleanBase = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;
  return `${cleanBase}/api/results/download/${filename}`;
}
