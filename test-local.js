// Simple test script to verify the API endpoints work locally
const fetch = require('node-fetch');

async function testAPI() {
  const baseUrl = 'http://localhost:3000';
  
  console.log('Testing VegaEdge API endpoints...\n');
  
  // Test bullish analysis
  try {
    console.log('Testing bullish analysis for AAPL...');
    const bullishResponse = await fetch(`${baseUrl}/api/analyze/bullish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticker: 'AAPL',
        min_dte: 30,
        max_dte: 90,
      }),
    });
    
    if (bullishResponse.ok) {
      const bullishData = await bullishResponse.json();
      console.log('✅ Bullish analysis successful');
      console.log('Summary preview:', bullishData.result?.summary?.substring(0, 100) + '...');
    } else {
      console.log('❌ Bullish analysis failed:', bullishResponse.status);
    }
  } catch (error) {
    console.log('❌ Bullish analysis error:', error.message);
  }
  
  console.log('\n' + '='.repeat(50) + '\n');
  
  // Test bearish analysis
  try {
    console.log('Testing bearish analysis for AAPL...');
    const bearishResponse = await fetch(`${baseUrl}/api/analyze/bearish`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ticker: 'AAPL',
        min_dte: 30,
        max_dte: 90,
      }),
    });
    
    if (bearishResponse.ok) {
      const bearishData = await bearishResponse.json();
      console.log('✅ Bearish analysis successful');
      console.log('Summary preview:', bearishData.result?.summary?.substring(0, 100) + '...');
    } else {
      console.log('❌ Bearish analysis failed:', bearishResponse.status);
    }
  } catch (error) {
    console.log('❌ Bearish analysis error:', error.message);
  }
  
  console.log('\nTest completed!');
}

// Only run if this script is executed directly
if (require.main === module) {
  testAPI().catch(console.error);
}

module.exports = { testAPI };
