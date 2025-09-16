import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { ticker, min_dte, max_dte } = req.body;

    // Validate input
    if (!ticker || !min_dte || !max_dte) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }

    // Call the Python serverless function directly
    const baseUrl = process.env.VERCEL_URL 
      ? `https://${process.env.VERCEL_URL}` 
      : 'http://localhost:3000';
    
    const response = await fetch(`${baseUrl}/api/analyze_bearish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticker,
        min_dte,
        max_dte,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Python function error:', errorText);
      return res.status(response.status).json({ 
        error: `Analysis error: ${response.status}` 
      });
    }

    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error('API error:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    });
  }
} 