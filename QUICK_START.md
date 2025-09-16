# Quick Start Guide - Deploy VegaEdge to Vercel

## 🚀 One-Click Deployment

### Option 1: Deploy with Vercel (Recommended)

1. **Push to GitHub/GitLab/Bitbucket**
   ```bash
   cd vegaedge-webapp
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin YOUR_REPO_URL
   git push -u origin main
   ```

2. **Deploy to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your repository
   - Click "Deploy" (Vercel auto-detects Next.js + Python)

3. **Done!** Your app will be live at `https://your-project.vercel.app`

### Option 2: Deploy with Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to project
cd vegaedge-webapp

# Deploy
vercel

# Follow prompts, then:
vercel --prod
```

## 🧪 Test Locally First

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Test the API (in another terminal)
node test-local.js
```

## 📁 Project Structure

```
vegaedge-webapp/
├── api/                          # Python serverless functions
│   ├── analysis_engine.py        # Core analysis logic
│   ├── analyze_bullish.py        # Bullish analysis endpoint
│   └── analyze_bearish.py        # Bearish analysis endpoint
├── pages/
│   ├── api/analyze/              # Next.js API routes
│   │   ├── bullish.ts            # Proxies to Python function
│   │   └── bearish.ts            # Proxies to Python function
│   └── index.tsx                 # Main UI
├── vercel.json                   # Vercel configuration
├── requirements.txt              # Python dependencies
└── package.json                  # Node.js dependencies
```

## 🔧 How It Works

1. **User Interface**: React/Next.js frontend with Tailwind CSS
2. **API Layer**: Next.js API routes that proxy to Python functions
3. **Analysis Engine**: Python serverless functions using yfinance
4. **Data Source**: Yahoo Finance (free, real-time options data)

## ⚡ Performance Notes

- **Cold Start**: First request may take 5-10 seconds
- **Analysis Time**: 5-15 seconds per analysis
- **Memory**: Uses ~200-500MB per function
- **Timeout**: 10s (hobby) / 60s (pro)

## 🐛 Troubleshooting

### Common Issues

1. **"Function not found"**
   - Check `vercel.json` configuration
   - Ensure Python files are in `/api/` directory

2. **"Import error"**
   - Verify `requirements.txt` has all dependencies
   - Check Python runtime version (3.9)

3. **"Timeout error"**
   - Analysis takes time, consider upgrading to Pro plan
   - Check Vercel function logs

4. **"No data found"**
   - Verify ticker symbol is valid
   - Check if options market exists for that ticker

### Debug Steps

1. **Check logs**: Vercel Dashboard > Functions > View Logs
2. **Test locally**: `vercel dev` then `node test-local.js`
3. **Verify dependencies**: Check `requirements.txt` is complete

## 💰 Pricing

- **Hobby Plan**: Free (10s timeout, 1024MB memory)
- **Pro Plan**: $20/month (60s timeout, better performance)

## 🎯 Next Steps

1. **Custom Domain**: Add your domain in Vercel settings
2. **Environment Variables**: Add any API keys if needed
3. **Monitoring**: Set up Vercel Analytics
4. **Optimization**: Consider caching for better performance

## 📞 Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Function Logs**: Check in Vercel dashboard
- **Local Testing**: Use `vercel dev` for debugging

---

**Ready to deploy?** Just push to GitHub and import to Vercel! 🚀
