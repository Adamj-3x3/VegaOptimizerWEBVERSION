# Railway Deployment Guide for VegaEdge Option Analyzer

This guide will help you deploy the VegaEdge Option Analyzer to Railway.

## Prerequisites

1. A Railway account (sign up at [railway.app](https://railway.app))
2. GitHub repository with the code
3. Railway CLI (optional but helpful)

## Quick Deployment

### Option 1: Deploy via Railway Dashboard

1. **Go to [railway.app](https://railway.app)**
2. **Sign up with GitHub**
3. **Click "Deploy from GitHub repo"**
4. **Select your `VegaOptimizerWEBVERSION` repository**
5. **Railway will auto-detect the setup and deploy**

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   ```

2. **Login to Railway:**
   ```bash
   railway login
   ```

3. **Deploy:**
   ```bash
   railway up
   ```

## Project Structure

```
vegaedge-webapp/
├── backend.py                    # FastAPI backend server
├── api/analyze/
│   └── analysis_engine.py        # Full Python analysis engine
├── pages/                        # Next.js frontend
├── requirements.txt              # Python dependencies
├── package.json                  # Node.js dependencies
├── railway.json                  # Railway configuration
└── nixpacks.toml                # Build configuration
```

## How It Works

1. **Frontend**: Next.js React app serves the UI
2. **Backend**: FastAPI server handles Python analysis
3. **Analysis Engine**: Full pandas/numpy/scipy analysis
4. **Data Source**: Yahoo Finance (yfinance library)

## Environment Variables

Railway will automatically set:
- `RAILWAY_URL` - Your backend URL
- `PORT` - Server port (usually 8000)

## Local Development

```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Run both frontend and backend
npm run dev:full

# Or run separately
npm run dev          # Frontend on :3000
npm run backend      # Backend on :8000
```

## Performance

- **Memory**: 512MB default (upgradeable)
- **CPU**: Shared (upgradeable)
- **Storage**: 1GB (upgradeable)
- **Network**: Unlimited
- **Dependencies**: Full pandas/numpy/scipy support

## Troubleshooting

### Common Issues

1. **Build fails**: Check `requirements.txt` and `package.json`
2. **Analysis errors**: Check yfinance data availability
3. **CORS issues**: Backend has CORS enabled for all origins

### Debugging

1. **Check Railway logs** in the dashboard
2. **Test backend directly**: `https://your-app.railway.app/health`
3. **Check environment variables** in Railway settings

## Cost

- **Hobby Plan**: $5/month (512MB RAM, 1GB storage)
- **Pro Plan**: $20/month (8GB RAM, 100GB storage)

## Support

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Discord**: Railway Discord community
- **GitHub Issues**: For code-related problems

---

**Ready to deploy?** Just connect your GitHub repo to Railway! 🚀
