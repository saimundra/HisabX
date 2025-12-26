import pytesseract
from PIL import Image
import io
import os
import re
import fitz 
from decimal import Decimal, InvalidOperation
from datetime import datetime
import difflib
from nepali_datetime import date as NepaliDate

# Advanced OCR patterns for data extraction - Enhanced for Indian GST invoices
AMOUNT_PATTERNS = [
    r'total\s*amount\s*:?\s*[$₹]?\s*(\d+(?:,\d{3})*\.?\d*)',  # Total Amount : 38026.00
    r'grand\s*total\s*:?\s*[$₹]?\s*(\d+(?:,\d{3})*\.?\d*)',  # Grand Total
    r'total\s*:?\s*[$₹]\s*(\d+(?:,\d{3})*\.?\d*)',  # TOTAL $154.06
    r'\$\s*(\d+(?:,\d{3})*\.?\d*)',  # $123.45, $1,234.56
    r'total\s*:?\s*₹?\$?(\d+(?:,\d{3})*\.?\d*)',  # Total: $123.45
    r'amount\s*:?\s*₹?\$?(\d+(?:,\d{3})*\.?\d*)',  # Amount: 123.45
    r'₹\s*(\d+(?:,\d{3})*\.?\d*)',  # ₹38026.00
]

TAX_PATTERNS = [
    r'vat\s*(?:\d+\.?\d*%)\s*[$₹]?\s*(\d+(?:,\d{3})*\.?\d*)',  # VAT 13% 59,696.00
    r'(?:sales\s*tax|tax)\s*(?:\d+\.?\d*%)\s*[$₹]?\s*(\d+(?:,\d{3})*\.?\d*)',  # Sales Tax 6.25% 9.06
    r'(?:cgst|sgst)\s*amt?\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)',  # CGST Amt: 2563.92
    r'(?:total\s*)?(?:gst|tax)\s*:?\s*[$₹]?\s*(\d+(?:,\d{3})*\.?\d*)',  # GST: 5127.84
    r'tax\s*:?\s*\$?(\d+(?:,\d{3})*\.?\d*)',
    r'vat\s*:?\s*\$?(\d+(?:,\d{3})*\.?\d*)',
]

DATE_PATTERNS = [
    r'(?:invoice\s+date|inv\.?\s*date|bill\s*date|date\s*of\s*invoice)\s*:?\s*(\d{8,10})',  # INVOICE DATE 11102019 or 1110212019 (no separators)
    r'(?:invoice\s+date|inv\.?\s*date|bill\s*date|date\s*of\s*invoice)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # Invoice Date : 11/02/2019
    r'(?:inv\.?\s*date|bill\s*date|date)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',  # Inv. Date : 10-01-25
    r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
    r'(\d{2,4}[-/]\d{1,2}[-/]\d{1,2})',
    r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})',
]

VENDOR_INDICATORS = [
    'store', 'market', 'shop', 'restaurant', 'cafe', 'gas', 'pharmacy',
    'hospital', 'clinic', 'hotel', 'airline', 'taxi', 'uber', 'lyft'
]

def words_to_number(text):
    """Convert written numbers to digits (e.g., 'six thousand nine hundred' -> 6900)"""
    word_to_num = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
        'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000,
        'lakh': 100000, 'lakhs': 100000, 'million': 1000000
    }
    
    # Remove "rupees", "only", etc.
    text = re.sub(r'\b(rupees?|only|and)\b', '', text, flags=re.IGNORECASE).strip()
    words = text.split()
    
    total = 0
    current = 0
    
    for word in words:
        word = word.lower().strip()
        if word in word_to_num:
            num = word_to_num[word]
            if num >= 1000:
                current = (current or 1) * num
                total += current
                current = 0
            elif num == 100:
                current = (current or 1) * num
            else:
                current += num
    
    total += current
    return total if total > 0 else None

def extract_text_from_image(image_file):
    """
    Extract text from image files or PDFs using OCR
    """
    try:
        file_path = str(image_file)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.pdf':
            # Handle PDF files
            return extract_text_from_pdf(file_path)
        else:
            # Handle image files
            return extract_text_from_image_file(file_path)
            
    except Exception as e:
        raise Exception(f"Error extracting text from file: {str(e)}")

def process_bill_image(image_file):
    """
    Extract and process bill data from image
    Returns structured data ready for Bill model
    """
    try:
        # Extract raw text
        raw_text = extract_text_from_image(image_file)
        
        # Process with advanced OCR functions
        structured_data = extract_bill_data(raw_text)
        
        # Return both raw text and processed data
        return {
            'ocr_text': raw_text,
            'vendor': structured_data.get('vendor'),
            'amount': structured_data.get('amount'),
            'tax_amount': structured_data.get('tax_amount'),
            'bill_date': structured_data.get('bill_date'),
            'invoice_number': structured_data.get('invoice_number'),
            'line_items': structured_data.get('line_items', [])
        }
        
    except Exception as e:
        raise Exception(f"Error processing bill image: {str(e)}")

def extract_bill_data(ocr_text):
    """Extract structured data from OCR text - Enhanced"""
    text_lower = ocr_text.lower()
    lines = ocr_text.split('\n')
    
    extracted_data = {
        'amount': extract_amount(text_lower, ocr_text),
        'tax_amount': extract_tax(text_lower, ocr_text),
        'vendor': extract_vendor(lines),
        'bill_date': extract_date(text_lower),
        'line_items': extract_line_items(lines),
        'invoice_number': extract_invoice_number(ocr_text),
        'gstin': extract_gstin(ocr_text),
        'subtotal': extract_subtotal(text_lower, ocr_text),
        'cgst': extract_cgst(text_lower, ocr_text),
        'sgst': extract_sgst(text_lower, ocr_text),
    }
    
    return extracted_data

def extract_amount(text, full_text=''):
    """Extract the main amount from text - improved"""
    amounts = []
    
    # First try to find "Grand Total" (highest priority)
    grand_total_pattern = r'grand\s*total\s*:?\s*[$₹]?\s*(\d+(?:,\d{3})*\.?\d*)'
    match = re.search(grand_total_pattern, text, re.IGNORECASE)
    if match:
        try:
            amount_str = match.group(1).replace(',', '')
            return Decimal(amount_str)
        except (InvalidOperation, IndexError):
            pass
    
    # Then try to find "Total Amount"
    total_amount_pattern = r'total\s*amount\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)'
    match = re.search(total_amount_pattern, text, re.IGNORECASE)
    if match:
        try:
            amount_str = match.group(1).replace(',', '')
            return Decimal(amount_str)
        except (InvalidOperation, IndexError):
            pass
    
    # Try to extract from "In Words" section (e.g., "Six thousand nine hundred")
    # This is a fallback when total amount is not in OCR
    words_pattern = r'in\s+words?:?\s*([a-z\s]+)'
    match = re.search(words_pattern, text, re.IGNORECASE)
    if match:
        amount_words = match.group(1).strip().lower()
        # Convert words to number
        amount_from_words = words_to_number(amount_words)
        if amount_from_words:
            return Decimal(amount_from_words)
    
    # Try to find "Total" followed by amount (with or without Rs./Ps. headers)
    # Pattern: Total | 6,900 or Total 6,900
    total_with_amount = r'total\s*[\|\s]+(\d+(?:,\d{3})*\.?\d*)'
    match = re.search(total_with_amount, text, re.IGNORECASE)
    if match:
        try:
            amount_str = match.group(1).replace(',', '')
            return Decimal(amount_str)
            return Decimal(amount_str)
        except (InvalidOperation, IndexError):
            pass
    
    # Try other patterns
    for pattern in AMOUNT_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                amount_str = match.group(1).replace(',', '')
                amount = Decimal(amount_str)
                amounts.append(amount)
            except (InvalidOperation, IndexError):
                continue
    
    # Return the largest amount found (likely the total)
    return max(amounts) if amounts else None

def extract_tax(text, full_text=''):
    """Extract tax amount - improved for Indian GST"""
    # Try to find total GST (CGST + SGST)
    cgst = extract_cgst(text, full_text)
    sgst = extract_sgst(text, full_text)
    
    if cgst and sgst:
        return cgst + sgst
    
    # Try general tax patterns
    for pattern in TAX_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return Decimal(match.group(1).replace(',', ''))
            except InvalidOperation:
                continue
    return None

def extract_vendor(lines):
    """Extract vendor name - improved for Indian GST invoices"""
    # Skip common header terms that are NOT vendor names (must match entire line)
    skip_exact_terms = [
        'tax invoice', 'invoice', 'bill', 'original', 'duplicate', 'original / duplicate',
        'original /duplicate', 'tax invoice original', 'tax invoice duplicate',
        'original /duplicate bill', 'tax invoice original /duplicate bill',
        'receipt', 'estimate', 'quotation', 'challan', 'proforma invoice'
    ]
    
    # Keywords that indicate this is NOT a vendor name
    skip_keywords = [
        'gstin', 'gst no', 'pan no', 'cin no', 'bill to', 'ship to', 'contact no',
        'due date', 'invoice date', 'invoice #', 'invoice no', 'p.o.#', 'terms',
        'buyer name', 'buyer', 'customer name', 'vat/pan no', 'address :',
        'issued to', 'date issued', 'billed to', 'sold to', 'issued by',  # Skip recipient/issuer labels
        'attention', 'attn:', 'client', 'customer',  # Skip attention/client labels
        '@', 'email', 'mail', '.com', '.net', '.org',  # Skip lines with email/website
        '|'  # Skip lines with pipe separators (usually contact info)
    ]
    
    candidates = []
    
    for i, line in enumerate(lines[:15]):  # Check first 15 lines
        line = line.strip()
        
        # Skip empty or very short lines
        if len(line) < 3:
            continue
        
        line_lower = line.lower()
        
        # Skip if entire line matches header terms
        if line_lower in skip_exact_terms:
            continue
        
        # Skip if line contains skip keywords
        if any(keyword in line_lower for keyword in skip_keywords):
            continue
        
        # Skip lines that are just numbers, dates, or symbols
        if re.match(r'^[\d\s\-/:,\.#\(\)]+$', line):
            continue
        
        # Skip address-like lines (start with # or contain plot/building/floor)
        if re.match(r'^[#\d]', line) or re.search(r'(?:plot|building|bldg|floor|street|road|cross|lane|avenue|drive)', line_lower):
            continue
        
        # Skip lines with contact info
        if re.search(r'(?:contact|phone|mobile|email|fax|tel)', line_lower):
            continue
        
        # Look for company names with Inc., LLC, Ltd., Corp., etc. (high confidence)
        if re.search(r'\b(?:inc\.?|llc|ltd\.?|corp\.?|pvt\.?|limited|corporation|company)\b', line_lower):
            score = 15
            if 1 <= i < 5:  # First few lines after header
                score += 5
            candidates.append((score, line))
        
        # Look for ALL CAPS company names (strong indicator)
        elif line.isupper() and len(line) > 5:
            # Should have at least 2 words or contain business indicators
            words = line.split()
            if len(words) >= 2 or any(indicator in line_lower for indicator in VENDOR_INDICATORS):
                # Give higher score to lines that appear after line 2 but before line 8
                score = 10
                if 2 <= i < 8:
                    score += 5
                if any(indicator in line_lower for indicator in VENDOR_INDICATORS):
                    score += 3
                candidates.append((score, line))
            # Also accept single-word ALL CAPS names (like ICONVIBE)
            elif len(words) == 1 and len(line) >= 5:
                score = 12  # High score for single-word brand names
                if i < 5:  # Very early in document
                    score += 8
                candidates.append((score, line))
        
        # Look for Title Case names (common for US companies like "East Repair Inc.")
        elif (line[0].isupper() and not line.isupper() and len(line) > 5):
            words = line.split()
            # Check if it's a proper company name (multiple capitalized words)
            capitalized_words = sum(1 for word in words if word and word[0].isupper())
            if capitalized_words >= 2 or any(indicator in line_lower for indicator in VENDOR_INDICATORS):
                score = 8
                if 1 <= i < 5:
                    score += 4
                if any(indicator in line_lower for indicator in VENDOR_INDICATORS):
                    score += 3
                candidates.append((score, line))
        
        # Check if line contains business type indicators
        elif any(indicator in line_lower for indicator in VENDOR_INDICATORS):
            if len(line.split()) >= 2:
                score = 7
                if 2 <= i < 8:
                    score += 3
                candidates.append((score, line))
    
    # Return the candidate with highest score
    if candidates:
        candidates.sort(reverse=True, key=lambda x: x[0])
        vendor_name = candidates[0][1]
        
        # Clean up vendor name - remove trailing special characters and OCR artifacts
        vendor_name = re.sub(r'[\[\]\{\}\(\)]+$', '', vendor_name)  # Remove trailing brackets
        vendor_name = re.sub(r'\s*[\d\]\|]+$', '', vendor_name)  # Remove trailing digits/pipes
        vendor_name = vendor_name.strip()
        
        return vendor_name
    
    return None

def extract_date(text):
    """Extract bill date - improved for multiple formats"""
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                date_str = match.group(1)
                
                # Handle 10-digit dates without separators 
                # Could be: MMDDYYYYYY (OCR error with extra digits)
                if len(date_str) == 10 and date_str.isdigit():
                    # Try MMDDYYYY format (month-day-year with 4-digit year)
                    try:
                        month = int(date_str[0:2])
                        day = int(date_str[2:4])
                        year = int(date_str[6:10])  # Last 4 digits
                        if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                            return datetime(year, month, day).date()
                    except (ValueError, IndexError):
                        pass
                    
                    # Alternative: try treating as MMDDYYYY (ignoring middle digits)
                    try:
                        month = int(date_str[0:2])
                        day = int(date_str[2:4])
                        # Try last 4 chars as year
                        year = int(date_str[-4:])
                        if 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100:
                            return datetime(year, month, day).date()
                    except (ValueError, IndexError):
                        pass
                
                # Handle 8-digit dates without separators (e.g., "11022019" or "02112019")
                elif len(date_str) == 8 and date_str.isdigit():
                    # Format: MMDDYYYY or DDMMYYYY
                    # Try MM/DD/YYYY first (common in US)
                    try:
                        month = int(date_str[0:2])
                        day = int(date_str[2:4])
                        year = int(date_str[4:8])
                        if 1 <= month <= 12 and 1 <= day <= 31:
                            return datetime(year, month, day).date()
                    except (ValueError, IndexError):
                        pass
                    
                    # Try DD/MM/YYYY format
                    try:
                        day = int(date_str[0:2])
                        month = int(date_str[2:4])
                        year = int(date_str[4:8])
                        if 1 <= month <= 12 and 1 <= day <= 31:
                            return datetime(year, month, day).date()
                    except (ValueError, IndexError):
                        pass
                
                # Try different date formats with separators
                date_formats = [
                    '%d-%m-%y',     # 10-01-25
                    '%d/%m/%y',     # 10/01/25
                    '%d-%m-%Y',     # 10-01-2025
                    '%d/%m/%Y',     # 10/01/2025
                    '%m/%d/%Y',     # 01/10/2025
                    '%m-%d-%Y',     # 01-10-2025
                    '%Y-%m-%d',     # 2025-01-10
                    '%B %d, %Y',    # January 10, 2025
                    '%b %d, %Y',    # Jan 10, 2025
                ]
                for fmt in date_formats:
                    try:
                        parsed_date = datetime.strptime(date_str, fmt).date()
                        
                        # Check if this is a Nepali date (Bikram Sambat)
                        # Nepali calendar years are typically 2000-2100 (BS)
                        # which corresponds to 1943-2043 AD approximately
                        if parsed_date.year >= 2070 and parsed_date.year <= 2100:
                            # This is likely a Nepali BS date, convert to AD
                            try:
                                nepali_date = NepaliDate(parsed_date.year, parsed_date.month, parsed_date.day)
                                ad_date = nepali_date.to_datetime_date()
                                return ad_date
                            except (ValueError, Exception) as e:
                                # If conversion fails, continue with original date
                                print(f"Nepali date conversion failed: {e}")
                                pass
                        
                        # If year is in 2-digit format, assume 20xx
                        if parsed_date.year < 2000:
                            parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                        return parsed_date
                    except ValueError:
                        continue
            except (IndexError, ValueError):
                continue
    return None

def extract_line_items(lines):
    """Extract individual line items - improved for structured tables"""
    items = []
    in_items_section = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        
        # Detect start of items section
        if any(keyword in line_lower for keyword in ['goods & service', 'description', 'item name', 'particulars', 'sr']):
            in_items_section = True
            continue
        
        # Detect end of items section
        if any(keyword in line_lower for keyword in ['sub-total', 'subtotal', 'summery', 'summary', 'bank details']):
            in_items_section = False
            break
        
        # Extract items
        if in_items_section and line.strip():
            # Look for lines with amount patterns (at least one decimal number)
            if re.search(r'\d+\.\d{2}', line):
                # Try to parse structured item data
                item_data = parse_item_line(line)
                if item_data:
                    items.append(item_data)
    
    return items[:20]  # Limit to first 20 items

def parse_item_line(line):
    """Parse a single line item into structured data"""
    try:
        # Pattern: Description Qty Unit Rate Taxable GST% GST_Amt Total
        # Example: "Best Ball Pen 2 Nos 10.00 20.00 2.40 22.40"
        
        parts = line.split()
        numbers = [p.replace(',', '') for p in parts if re.match(r'^\d+(?:\.\d{2})?$', p.replace(',', ''))]
        
        if len(numbers) >= 3:
            # Extract description (text before numbers)
            desc_parts = []
            for part in parts:
                if not re.match(r'^\d+(?:\.\d{2})?$', part.replace(',', '')):
                    desc_parts.append(part)
                else:
                    break
            
            description = ' '.join(desc_parts).strip()
            
            # Simple heuristic: last number is total, before that is taxable amount
            return {
                'description': description,
                'quantity': numbers[0] if len(numbers) > 0 else None,
                'rate': numbers[1] if len(numbers) > 1 else None,
                'amount': numbers[-1] if len(numbers) > 0 else None,
                'raw_line': line
            }
    except Exception:
        pass
    
    return None

def extract_invoice_number(text):
    """Extract invoice/bill number - improved for various formats"""
    patterns = [
        r'invoice\s+no\.?\s*[>:]\s*([a-zA-Z0-9\-_/.]+)',  # Invoice No. > BSB.O111 or Invoice No: ABC123
        r'invoice\s+number\s*:?\s*([a-zA-Z0-9\-_/.]+)',  # Invoice Number: INV-12345 (with flexible whitespace)
        r'bill\s*no\.?\s*[>:]?\s*([a-zA-Z0-9\-_/.]+)',  # Bill No 1 or Bill No: 1 or Bill No. > 123
        r'invoice\s*#\s*:?\s*([a-zA-Z0-9\-_/.]+)',  # INVOICE # us-001
        r'inv\.?\s*no\.?\s*[>:]?\s*([a-zA-Z0-9\-_/.]+)',  # Inv. No. : Inv-5 or Inv No > 123
        r'invoice\s*(?:no|num)\.?\s*:?\s*([a-zA-Z0-9\-_/.]+)',  # Invoice No: ABC123 or Invoice No.
        r'bill\s*(?:number|#)\.?\s*:?\s*([a-zA-Z0-9\-_/.]+)',  # Bill Number: 12345
        r'#\s*:?\s*([a-zA-Z]{2,}-?\d+)',  # # US-001 or #: us-001
        r'invoice\s*:?\s*([a-zA-Z0-9]{3,}(?:[\-_/.][a-zA-Z0-9]+)?)',  # Invoice: INV001
        # Fallback: Look for "Bill" followed by standalone number on same or next line
        r'bill[^\n]{0,30}?(\d{1,6})',  # Bill ... 123
    ]
    
    # Common words that are NOT invoice numbers (to filter out false positives)
    blacklist = ['date', 'ltd', 'limited', 'inc', 'corp', 'pvt', 'llc', 'company', 'co']
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            inv_num = match.group(1).strip()
            # Remove extra whitespace
            inv_num = re.sub(r'\s+', '', inv_num)
            
            # Check if it's in the blacklist
            if inv_num.lower() in blacklist:
                continue
            
            # For fallback pattern (last one), be more strict - avoid dates
            if i == len(patterns) - 1:
                # Skip if it looks like a date (4+ digits or contains separators)
                if len(inv_num) >= 4 or '-' in inv_num or '/' in inv_num:
                    continue
            
            # Ensure it's not too long and not too short
            # Allow pure numbers or alphanumeric with at least one digit
            if 1 <= len(inv_num) <= 30 and (inv_num.isdigit() or any(char.isdigit() for char in inv_num)):
                return inv_num.upper()  # Normalize to uppercase
    
    return None

def extract_gstin(text):
    """Extract GSTIN (GST Identification Number)"""
    # GSTIN format: 2 digits + 10 alphanumeric + 1 letter + 1 number + 1 letter + 1 alphanumeric
    pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}\b'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    
    # Simplified pattern for OCR errors
    pattern = r'\b\d{2}[A-Z0-9]{13}\b'
    match = re.search(pattern, text)
    if match:
        return match.group(0)
    
    return None

def extract_subtotal(text, full_text=''):
    """Extract subtotal (before tax)"""
    patterns = [
        r'sub-total\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)',
        r'subtotal\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)',
        r'taxable\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return Decimal(match.group(1).replace(',', ''))
            except InvalidOperation:
                continue
    return None

def extract_cgst(text, full_text=''):
    """Extract CGST amount"""
    pattern = r'cgst\s*amt?\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return Decimal(match.group(1).replace(',', ''))
        except InvalidOperation:
            pass
    return None

def extract_sgst(text, full_text=''):
    """Extract SGST amount"""
    pattern = r'sgst\s*amt?\s*:?\s*₹?\s*(\d+(?:,\d{3})*\.?\d*)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        try:
            return Decimal(match.group(1).replace(',', ''))
        except InvalidOperation:
            pass
    return None

def categorize_bill(bill_data, categories):
    """Auto-categorize bill based on vendor and content"""
    vendor = bill_data.get('vendor', '').lower()
    ocr_text = bill_data.get('ocr_text', '').lower()
    
    best_match = None
    highest_score = 0
    
    for category in categories:
        score = 0
        keywords = category.get_keywords_list()
        
        # Check vendor match
        for keyword in keywords:
            if keyword in vendor:
                score += 3
            elif keyword in ocr_text:
                score += 1
        
        # Fuzzy matching for vendor
        if vendor:
            for keyword in keywords:
                similarity = difflib.SequenceMatcher(None, keyword, vendor).ratio()
                if similarity > 0.8:
                    score += 2
        
        if score > highest_score:
            highest_score = score
            best_match = category
    
    confidence = min(highest_score / 5.0, 1.0)  # Normalize to 0-1
    return best_match, confidence

def extract_text_from_image_file(image_path):
    """Extract text from image files using OCR"""
    try:
        # Open the image file
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using pytesseract
        extracted_text = pytesseract.image_to_string(image)
        
        return extracted_text.strip()
    
    except Exception as e:
        raise Exception(f"Error extracting text from image: {str(e)}")

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF files using PyMuPDF"""
    try:
        # Open PDF document
        doc = fitz.open(pdf_path)
        extracted_text = ""
        
        # Extract text from each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_text = page.get_text()
            extracted_text += page_text + "\n"
        
        doc.close()
        
        # If PDF text extraction fails or returns minimal text, try OCR
        if len(extracted_text.strip()) < 50:
            extracted_text = extract_text_from_pdf_with_ocr(pdf_path)
        
        return extracted_text.strip()
    
    except Exception as e:
        # If PyMuPDF fails, try OCR on PDF pages
        try:
            return extract_text_from_pdf_with_ocr(pdf_path)
        except Exception as ocr_error:
            raise Exception(f"PDF text extraction failed: {str(e)}, OCR also failed: {str(ocr_error)}")

def extract_text_from_pdf_with_ocr(pdf_path):
    """Extract text from PDF using OCR (for scanned PDFs)"""
    try:
        doc = fitz.open(pdf_path)
        extracted_text = ""
        
        for page_num in range(min(3, len(doc))):  # Process max 3 pages for performance
            page = doc.load_page(page_num)
            
            # Convert page to image
            pix = page.get_pixmap()
            img_data = pix.tobytes("png")
            
            # Use PIL to process the image
            image = Image.open(io.BytesIO(img_data))
            
            # Extract text using OCR
            page_text = pytesseract.image_to_string(image)
            extracted_text += page_text + "\n"
        
        doc.close()
        return extracted_text.strip()
    
    except Exception as e:
        raise Exception(f"OCR extraction from PDF failed: {str(e)}")