# Vercel Deployment Guide for VegaEdge Option Analyzer

This guide will help you deploy the VegaEdge Option Analyzer to Vercel.

## Prerequisites

1. A Vercel account (sign up at [vercel.com](https://vercel.com))
2. Git repository (GitHub, GitLab, or Bitbucket)
3. The code should be pushed to your repository

## Deployment Steps

### 1. Prepare Your Repository

Make sure all the files are in your repository:
- `api/analysis_engine.py` - Python analysis engine
- `api/analyze_bullish.py` - Bullish analysis serverless function
- `api/analyze_bearish.py` - Bearish analysis serverless function
- `vercel.json` - Vercel configuration
- `requirements.txt` - Python dependencies
- All Next.js files (pages, components, etc.)

### 2. Deploy to Vercel

#### Option A: Deploy via Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "New Project"
3. Import your Git repository
4. Vercel will automatically detect it's a Next.js project
5. Click "Deploy"

#### Option B: Deploy via Vercel CLI

1. Install Vercel CLI:
   ```bash
   npm i -g vercel
   ```

2. Navigate to your project directory:
   ```bash
   cd vegaedge-webapp
   ```

3. Login to Vercel:
   ```bash
   vercel login
   ```

4. Deploy:
   ```bash
   vercel
   ```

5. Follow the prompts to configure your project

### 3. Configure Environment Variables (if needed)

If you need any environment variables:
1. Go to your project dashboard on Vercel
2. Navigate to Settings > Environment Variables
3. Add any required variables

### 4. Test Your Deployment

Once deployed, your app will be available at:
- Production: `https://your-project-name.vercel.app`
- Preview: `https://your-project-name-git-branch.vercel.app`

Test the functionality by:
1. Entering a ticker symbol (e.g., "AAPL")
2. Setting date range (e.g., 30-90 days)
3. Selecting bullish or bearish strategy
4. Clicking "Analyze"

## Project Structure

```
vegaedge-webapp/
├── api/
│   ├── analysis_engine.py      # Core Python analysis logic
│   ├── analyze_bullish.py      # Bullish analysis serverless function
│   └── analyze_bearish.py      # Bearish analysis serverless function
├── pages/
│   ├── api/
│   │   └── analyze/
│   │       ├── bullish.ts      # Next.js API route (calls Python function)
│   │       └── bearish.ts      # Next.js API route (calls Python function)
│   └── index.tsx               # Main UI component
├── vercel.json                 # Vercel configuration
├── requirements.txt            # Python dependencies
└── package.json               # Node.js dependencies
```

## How It Works

1. **Frontend**: Next.js React app with Tailwind CSS
2. **API Routes**: Next.js API routes that proxy requests to Python functions
3. **Python Functions**: Serverless Python functions that perform the analysis
4. **Data Source**: Yahoo Finance (yfinance library)

## Troubleshooting

### Common Issues

1. **Python Dependencies**: Make sure `requirements.txt` includes all necessary packages
2. **Function Timeout**: Vercel has a 10-second timeout for hobby plans, 60 seconds for pro
3. **Memory Limits**: Hobby plan has 1024MB memory limit
4. **Cold Starts**: First request might be slower due to cold start

### Debugging

1. Check Vercel function logs in the dashboard
2. Use `console.log()` in your functions for debugging
3. Test locally with `vercel dev` before deploying

## Performance Considerations

- The analysis can take 5-15 seconds depending on the ticker
- Vercel functions have cold starts, so first requests might be slower
- Consider upgrading to Pro plan for better performance and longer timeouts

## Cost

- **Hobby Plan**: Free with limitations (10s timeout, 1024MB memory)
- **Pro Plan**: $20/month with better performance and longer timeouts

## Support

If you encounter issues:
1. Check Vercel function logs
2. Test locally with `vercel dev`
3. Verify all dependencies are in `requirements.txt`
4. Check that Python functions are properly configured in `vercel.json`
