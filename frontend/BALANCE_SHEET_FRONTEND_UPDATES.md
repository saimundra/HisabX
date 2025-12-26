# Balance Sheet Frontend Updates

## Summary
Updated the frontend to support the new Nepal Standard Balance Sheet format with automatic year-over-year comparison.

## Changes Made

### 1. FinancialDashboard.js
**File**: `src/components/features/dashboard/FinancialDashboard/FinancialDashboard.js`

**Updated `downloadBalanceSheet` function** (around line 74):
- Now automatically calculates comparison date (previous year)
- Sends both `as_of_date` and `comparison_date` to backend
- Backend will generate PDF with side-by-side comparison

**Changes**:
```javascript
// Before
const response = await api.get('/financial/balance-sheet/', {
  params: { as_of_date: asOfDate, format },
  ...
});

// After
const comparisonDate = new Date(asOfDate);
comparisonDate.setFullYear(comparisonDate.getFullYear() - 1);
const comparisonDateStr = comparisonDate.toISOString().split('T')[0];

const response = await api.get('/financial/balance-sheet/', {
  params: { 
    as_of_date: asOfDate, 
    comparison_date: comparisonDateStr,
    format 
  },
  ...
});
```

### 2. BalanceSheet.js
**File**: `src/components/features/dashboard/FinancialDashboard/BalanceSheet.js`

**Updated button labels and added help text**:
- Changed "Download PDF" → "Download PDF (Nepal Format)"
- Added informational note about Nepal Standard format
- Added tooltips to buttons explaining the format

**Changes**:
```javascript
// Added note below date
<p className="nepal-format-note">
  📋 PDF export follows Nepal Standard Accounting Format 
  with schedule numbers and year-over-year comparison
</p>

// Updated button text
📄 Download PDF (Nepal Format)
```

## Features

### Automatic Comparison Year
- When user downloads balance sheet for any date (e.g., 2025-12-31)
- Frontend automatically calculates previous year (2024-12-31)
- Backend generates PDF with both columns side-by-side

### User Experience
- Clear indication that PDF uses Nepal Standard format
- Tooltips on hover explaining the format
- No extra user input required - comparison is automatic

## How It Works

1. **User selects period** (Monthly/Quarterly/Yearly)
2. **User clicks "Download PDF (Nepal Format)"**
3. **Frontend calculates**:
   - Current date: Based on selected period
   - Comparison date: Exactly 1 year before current date
4. **Backend generates**:
   - Nepal Standard format
   - Schedule numbers (1-12)
   - Two-column comparison
   - Professional grid layout
5. **User receives**: PDF matching the scanned Nepal balance sheet format

## Example Dates

| Selected Period | As Of Date | Comparison Date |
|----------------|------------|-----------------|
| Dec 2025 | 2025-12-31 | 2024-12-31 |
| Q4 2025 | 2025-12-31 | 2024-12-31 |
| Year 2025 | 2025-12-31 | 2024-12-31 |
| Sep 2025 | 2025-09-30 | 2024-09-30 |
| Q3 2025 | 2025-09-30 | 2024-09-30 |

## Testing

### Test the changes:

1. **Start frontend**:
   ```bash
   cd /Users/saimundragodar/Desktop/internship/Mproject/frontend
   npm start
   ```

2. **Navigate to Financial Dashboard**:
   - Login to your account
   - Go to Dashboard → Financial Dashboard
   - Select "Balance Sheet" tab

3. **Test PDF download**:
   - Select any period (Monthly/Quarterly/Yearly)
   - Click "Download PDF (Nepal Format)"
   - Verify PDF has:
     - ✅ Four columns (Assets, Schedule, Current Year, Previous Year)
     - ✅ Schedule numbers (1-12)
     - ✅ Proper grouping (Non-Current, Current)
     - ✅ Two years of data
     - ✅ Professional grid layout
     - ✅ Footer with schedules note

4. **Test Excel download**:
   - Click "Download Excel"
   - Verify Excel format (existing format, not changed)

## Browser Compatibility

Works on all modern browsers:
- ✅ Chrome/Edge
- ✅ Firefox
- ✅ Safari

## API Endpoint

**Balance Sheet Endpoint**: `GET /api/financial/balance-sheet/`

**Parameters**:
- `as_of_date` (required): Date in YYYY-MM-DD format
- `comparison_date` (optional): Previous year date in YYYY-MM-DD format
  - If not provided, backend uses 1 year before `as_of_date`
- `format` (required): `pdf` | `excel` | `json`

**Example Request**:
```
GET /api/financial/balance-sheet/?as_of_date=2025-12-31&comparison_date=2024-12-31&format=pdf
```

## Files Modified

1. ✅ `frontend/src/components/features/dashboard/FinancialDashboard/FinancialDashboard.js`
   - Updated `downloadBalanceSheet` function
   - Added comparison date calculation

2. ✅ `frontend/src/components/features/dashboard/FinancialDashboard/BalanceSheet.js`
   - Updated button labels
   - Added Nepal format notice
   - Added tooltips

## No Breaking Changes

- ✅ Existing Excel export unchanged
- ✅ JSON API response unchanged
- ✅ Backward compatible (comparison_date is optional)
- ✅ All existing functionality preserved

## Future Enhancements

1. **Manual comparison date picker**:
   - Add option for users to select custom comparison period
   - Dropdown to choose: "Compare with last year" vs "Custom date"

2. **Multiple comparison years**:
   - Support 3+ year comparison
   - Add/remove comparison columns dynamically

3. **Format preferences**:
   - Save user preference for default format
   - Option to always use Nepal format or alternate format

4. **Preview before download**:
   - Show PDF preview in modal before downloading
   - Allow users to verify data before saving

## Notes

- The Nepal format PDF is generated server-side using ReportLab
- Comparison date defaults to 1 year prior if not specified
- Format follows the exact layout from `rajendrabalancesheet.jpg`
- Schedule numbers match Nepal accounting standards
