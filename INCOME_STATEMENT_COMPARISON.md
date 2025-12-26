# Income Statement Format Comparison

## Date: December 21, 2025

This document compares the **Nepal Standard Income Statement** format (as seen in reference images) with our **Current System Implementation**.

---

## 🇳🇵 Nepal Standard Format (Expected)

Based on the Nepal Accounting Standards and similar to the Balance Sheet format you provided:

### Structure:
```
                    [Company Name]
              Statement of Profit or Loss
        For the year ended [Date] (Chaitra XX, 20XX)

┌─────────────────────────────────────────┬──────────┬────────────────┬────────────────┐
│ Particulars                             │ Schedule │ Current Year   │ Previous Year  │
│                                         │          │      Rs.       │      Rs.       │
├─────────────────────────────────────────┼──────────┼────────────────┼────────────────┤
│ Revenue from Operations                 │    10    │   XX,XXX.XX    │   XX,XXX.XX    │
│ Other Income                            │    11    │    X,XXX.XX    │    X,XXX.XX    │
├─────────────────────────────────────────┼──────────┼────────────────┼────────────────┤
│ Total Revenue                           │          │   XX,XXX.XX    │   XX,XXX.XX    │
├─────────────────────────────────────────┼──────────┼────────────────┼────────────────┤
│                                         │          │                │                │
│ EXPENSES:                               │          │                │                │
│ Cost of Sales                           │    12    │   XX,XXX.XX    │   XX,XXX.XX    │
│ Administrative Expenses                 │    13    │    X,XXX.XX    │    X,XXX.XX    │
│ Selling and Distribution Expenses       │    14    │    X,XXX.XX    │    X,XXX.XX    │
│ Finance Costs                           │    15    │      XXX.XX    │      XXX.XX    │
│ Depreciation & Amortization             │    16    │    X,XXX.XX    │    X,XXX.XX    │
├─────────────────────────────────────────┼──────────┼────────────────┼────────────────┤
│ Total Expenses                          │          │   XX,XXX.XX    │   XX,XXX.XX    │
├─────────────────────────────────────────┼──────────┼────────────────┼────────────────┤
│                                         │          │                │                │
│ Profit/(Loss) Before Tax                │          │    X,XXX.XX    │    X,XXX.XX    │
│                                         │          │                │                │
│ Less: Income Tax Expense                │    17    │      XXX.XX    │      XXX.XX    │
├─────────────────────────────────────────┼──────────┼────────────────┼────────────────┤
│ Profit/(Loss) for the Year              │          │    X,XXX.XX    │    X,XXX.XX    │
└─────────────────────────────────────────┴──────────┴────────────────┴────────────────┘

Schedules 10 to 17 form integral part of financial statements.

Earnings Per Share (EPS):                           XXX.XX           XXX.XX
```

### Key Features:
1. **4-Column Layout**: Particulars | Schedule | Current Year Rs. | Previous Year Rs.
2. **Schedule Numbers**: 10-17 for Income Statement line items
3. **Two-Year Comparison**: Side-by-side comparison (not just current year)
4. **Nepal Rupees (Rs.)**: Currency denomination in NPR
5. **Tax Calculation**: Explicit "Profit Before Tax" and "Income Tax Expense" lines
6. **EPS Calculation**: Earnings per share at the bottom
7. **Schedule Reference**: Footer note about schedules forming integral part
8. **BS Date Support**: Should support both AD and BS (Bikram Sambat) dates

---

## 💻 Current System Implementation

### Structure:
```
                    [User Name]
              Income Statement (Profit & Loss)
              Period: [Start Date] to [End Date]

┌─────────────────────────────────────────┬────────────────┐
│ Description                             │     Amount     │
├─────────────────────────────────────────┼────────────────┤
│ REVENUE                                 │                │
├─────────────────────────────────────────┼────────────────┤
│ Total Revenue                           │   XX,XXX.XX    │
├─────────────────────────────────────────┼────────────────┤
│                                         │                │
│ EXPENSES                                │                │
├─────────────────────────────────────────┼────────────────┤
│ [Category 1]                            │    X,XXX.XX    │
│ [Category 2]                            │    X,XXX.XX    │
│ [Category 3]                            │    X,XXX.XX    │
├─────────────────────────────────────────┼────────────────┤
│ Total Expenses                          │   XX,XXX.XX    │
├─────────────────────────────────────────┼────────────────┤
│                                         │                │
│ NET INCOME                              │    X,XXX.XX    │
├─────────────────────────────────────────┼────────────────┤
│ Profit Margin                           │      XX.XX%    │
└─────────────────────────────────────────┴────────────────┘
```

### Key Features:
1. **2-Column Layout**: Description | Amount (ONLY current period)
2. **No Schedule Numbers**: Missing standardized schedule references
3. **Single Period**: Only shows current period data (no comparison)
4. **Simple Categorization**: Basic expense categories without schedules
5. **No Tax Breakdown**: Direct calculation from Revenue - Expenses
6. **No EPS**: Earnings per share not calculated
7. **Generic Format**: Not aligned with Nepal Accounting Standards

---

## 📊 Key Differences

| Feature | Nepal Standard (Expected) | Current System | Status |
|---------|---------------------------|----------------|--------|
| **Columns** | 4 columns (Particulars, Schedule, Current, Previous) | 2 columns (Description, Amount) | ❌ Missing |
| **Schedule Numbers** | Yes (10-17 for P&L) | No | ❌ Missing |
| **Year Comparison** | Side-by-side comparison | Single period only | ❌ Missing |
| **Currency** | Nepal Rupees (Rs.) | USD ($) | ⚠️ Wrong |
| **Tax Breakdown** | Profit Before Tax + Tax Expense | Direct Net Income | ❌ Missing |
| **EPS Calculation** | Yes | No | ❌ Missing |
| **Schedule Footer** | "Schedules 10 to 17 form integral part..." | None | ❌ Missing |
| **BS Date Support** | Both AD and BS dates | Only AD dates | ❌ Missing |
| **Revenue Breakdown** | Operations + Other Income (separate) | Single revenue line | ⚠️ Simplified |
| **Expense Categories** | Standardized (Cost of Sales, Admin, Selling, Finance) | Dynamic categories from bills | ⚠️ Different |

---

## 🎯 Required Changes

### Backend Changes:

1. **Create `NepalIncomeStatementExporter` class** (similar to `NepalBalanceSheetExporter`)
   - Location: `backend/reports/nepal_income_statement_exporter.py`
   - 4-column table layout
   - Schedule numbers 10-17
   - Previous year comparison support

2. **Update `financial_statements.py`**:
   - Add comparison period support
   - Add tax calculation fields
   - Add EPS calculation
   - Structured revenue breakdown (Operations vs Other Income)
   - Standardized expense categories with schedule mapping

3. **Update `views.py`**:
   - Add `comparison_start_date` and `comparison_end_date` parameters
   - Use `NepalIncomeStatementExporter` for PDF generation
   - Support both AD and BS dates

4. **Database Schema**:
   - Consider adding `IncomeStatementSchedule` model for schedule mappings
   - Add fields for tax-related information in bills

### Frontend Changes:

1. **Update `IncomeStatement.js`**:
   - Change from 2-column to 4-column layout
   - Add Schedule column
   - Add Previous Year column
   - Display schedule numbers
   - Add schedule footer note
   - Change currency symbol from $ to Rs.

2. **Update `FinancialDashboard.js`**:
   - Add comparison period selection (like balance sheet)
   - Calculate previous year dates automatically
   - Pass comparison data to IncomeStatement component

---

## 📋 Schedule Mapping (Nepal Standard)

### Income Statement Schedules:
- **Schedule 10**: Revenue from Operations
- **Schedule 11**: Other Income
- **Schedule 12**: Cost of Sales
- **Schedule 13**: Administrative Expenses
- **Schedule 14**: Selling and Distribution Expenses
- **Schedule 15**: Finance Costs
- **Schedule 16**: Depreciation & Amortization
- **Schedule 17**: Income Tax Expense

### Balance Sheet Schedules (Already Implemented):
- **Schedule 1**: Property, Plant & Equipment
- **Schedule 2**: Intangible Assets
- **Schedule 3**: Investments
- **Schedule 4**: Trade & Other Receivables
- **Schedule 5**: Cash & Cash Equivalents
- **Schedule 6**: Share Capital
- **Schedule 7**: Long-term Borrowings
- **Schedule 8**: Provisions
- **Schedule 9**: Trade & Other Payables

---

## 🚀 Implementation Priority

### High Priority (Core Nepal Format):
1. ✅ 4-column layout (Particulars, Schedule, Current, Previous)
2. ✅ Schedule numbers (10-17)
3. ✅ Previous year comparison
4. ✅ Currency change ($ → Rs.)
5. ✅ Schedule footer note

### Medium Priority (Accounting Compliance):
6. ⚠️ Tax breakdown (Profit Before Tax + Tax)
7. ⚠️ Standardized expense categories
8. ⚠️ Revenue breakdown (Operations + Other)

### Low Priority (Advanced Features):
9. 🔄 EPS calculation
10. 🔄 BS (Bikram Sambat) date support
11. 🔄 Detailed schedule pages (separate PDFs for each schedule)

---

## 📝 Sample Nepal Format Output

```
                        ABC Company Pvt. Ltd.
                    Statement of Profit or Loss
              For the year ended Chaitra 32, 2081 (March 31, 2025)

┌──────────────────────────────────┬──────────┬──────────────┬──────────────┐
│ Particulars                      │ Schedule │ 2024-25 Rs.  │ 2023-24 Rs.  │
├──────────────────────────────────┼──────────┼──────────────┼──────────────┤
│ Revenue from Operations          │    10    │  5,000,000   │  4,500,000   │
│ Other Income                     │    11    │    100,000   │     80,000   │
├──────────────────────────────────┼──────────┼──────────────┼──────────────┤
│ Total Revenue                    │          │  5,100,000   │  4,580,000   │
├──────────────────────────────────┼──────────┼──────────────┼──────────────┤
│ EXPENSES:                        │          │              │              │
│ Cost of Sales                    │    12    │  2,500,000   │  2,200,000   │
│ Administrative Expenses          │    13    │    800,000   │    750,000   │
│ Selling & Distribution Expenses  │    14    │    400,000   │    380,000   │
│ Finance Costs                    │    15    │     50,000   │     45,000   │
│ Depreciation & Amortization      │    16    │    150,000   │    140,000   │
├──────────────────────────────────┼──────────┼──────────────┼──────────────┤
│ Total Expenses                   │          │  3,900,000   │  3,515,000   │
├──────────────────────────────────┼──────────┼──────────────┼──────────────┤
│ Profit Before Tax                │          │  1,200,000   │  1,065,000   │
│ Less: Income Tax Expense         │    17    │    300,000   │    266,250   │
├──────────────────────────────────┼──────────┼──────────────┼──────────────┤
│ Profit for the Year              │          │    900,000   │    798,750   │
└──────────────────────────────────┴──────────┴──────────────┴──────────────┘

Schedules 10 to 17 form integral part of financial statements.

Earnings Per Share (Basic):                         90.00          79.88
```

---

## 📸 Visual Comparison

### Current System (Web Display):
- Simple 2-column table
- Single period
- USD currency
- No schedules
- Generic expense categories

### Nepal Standard (Expected):
- Professional 4-column table
- Two-year comparison
- NPR currency (Rs.)
- Schedule numbers for audit trail
- Standardized categories per Nepal Accounting Standards
- Tax breakdown
- EPS calculation

---

## 🔍 Next Steps

1. **Review the reference image** (rajendraincomestatement.DNG) to confirm exact format
2. **Create `NepalIncomeStatementExporter.py`** with Nepal format
3. **Update backend services** for comparison period support
4. **Update frontend `IncomeStatement.js`** to match Nepal format
5. **Test with real data** to ensure accuracy
6. **Add schedule detail pages** (optional, for compliance)

---

**Note**: This comparison is based on Nepal Accounting Standards and the Balance Sheet format you provided. The exact format from your reference image (rajendraincomestatement.DNG) should be reviewed to confirm specific layout details, but the general structure should match the Nepal Standard format described above.
