# Demand Forecasting — Business Summary

## What Drives Demand

| Driver | Impact |
|--------|--------|
| **Promotions** | **+12–16% uplift** on average across all SKUs and supermarkets during promotional weeks |
| **SKU mix** | Organic Milk is the highest-volume SKU (238K total units), followed by Whole Wheat Bread and Free Range Eggs |
| **Market variability** | DailyNeeds is the highest-volume supermarket (219K total), nearly 2x GreenBasket |
| **Seasonality** | Demand varies by month — peak demand months differ by SKU, with clear trough periods |
| **Year-over-year trends** | Demand direction differs by SKU — some trending up, some flat, none declining sharply |

## Forecast Accuracy

**Model:** LightGBM direct multi-step (8-week horizon)

**Error rate:** **9.34% WAPE** (Weighted Absolute Percentage Error)

This means: on an average weekly demand of ~459 units, the forecast is typically off by **~43 units** per week.

The model uses:
- Historical demand patterns (lag features up to 52 weeks)
- Rolling averages and trends
- Promotion timing
- Calendar effects (month, quarter, week-of-year)
- SKU and market identity

## Business Implications

### Stock-outs
- With 9% error, **safety stock of ~1 week of demand** covers most forecast uncertainty
- Legacy rule-of-thumb stock-outs (pessimistic ordering) can be cut by identifying low-risk weeks
- Promo weeks flagged in advance allow pre-positioning inventory to avoid stock-outs on high-lift items

### Write-offs
- Over-ordering risk is highest on low-volume series (Free Range Eggs at smaller markets) where percentage error translates to minimal absolute waste
- The 8-week horizon enables **just-in-time replenishment planning** rather than bulk forward-buying
- Seasonal trough periods can be identified 2 months ahead, allowing inventory reduction before low-demand windows

### Recommendation
- Integrate forecast into weekly replenishment with a **1.15× confidence buffer** (covers ~85% of error)
- Flag promo weeks at +12% baseline reorder point in advance
- Review SKU×Market forecasts monthly to capture any drift in demand patterns
