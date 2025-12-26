/**
 * Nepali Date (Bikram Sambat) Conversion Utilities
 * Handles conversion between AD and BS dates
 */

import NepaliDate from 'nepali-date-converter';

/**
 * Convert AD date to BS date
 * @param {string|Date} adDate - AD date (YYYY-MM-DD or Date object)
 * @returns {string} BS date in YYYY-MM-DD format
 */
export const adToBS = (adDate) => {
  try {
    const date = typeof adDate === 'string' ? new Date(adDate) : adDate;
    const nepaliDate = new NepaliDate(date);
    const year = nepaliDate.getYear();
    const month = String(nepaliDate.getMonth() + 1).padStart(2, '0');
    const day = String(nepaliDate.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  } catch (error) {
    console.error('Error converting AD to BS:', error);
    return '';
  }
};

/**
 * Convert BS date to AD date
 * @param {string} bsDate - BS date in YYYY-MM-DD format
 * @returns {string} AD date in YYYY-MM-DD format
 */
export const bsToAD = (bsDate) => {
  try {
    const [year, month, day] = bsDate.split('-').map(Number);
    const nepaliDate = new NepaliDate(year, month - 1, day);
    const adDate = nepaliDate.toJsDate();
    return adDate.toISOString().split('T')[0];
  } catch (error) {
    console.error('Error converting BS to AD:', error);
    return '';
  }
};

/**
 * Format BS date for display
 * @param {string} bsDate - BS date in YYYY-MM-DD format
 * @returns {string} Formatted BS date (YYYY साल MM महिना DD गते)
 */
export const formatBSDate = (bsDate) => {
  try {
    const [year, month, day] = bsDate.split('-');
    const nepaliMonths = [
      'बैशाख', 'जेष्ठ', 'आषाढ', 'श्रावण', 'भाद्र', 'आश्विन',
      'कार्तिक', 'मंसिर', 'पौष', 'माघ', 'फाल्गुन', 'चैत्र'
    ];
    return `${year} ${nepaliMonths[parseInt(month) - 1]} ${day}`;
  } catch (error) {
    return bsDate;
  }
};

/**
 * Format AD date for display
 * @param {string|Date} adDate - AD date
 * @returns {string} Formatted AD date (DD MMM YYYY)
 */
export const formatADDate = (adDate) => {
  try {
    const date = typeof adDate === 'string' ? new Date(adDate) : adDate;
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  } catch (error) {
    return adDate;
  }
};

/**
 * Get current BS date
 * @returns {string} Current BS date in YYYY-MM-DD format
 */
export const getCurrentBSDate = () => {
  return adToBS(new Date());
};

/**
 * Get current AD date
 * @returns {string} Current AD date in YYYY-MM-DD format
 */
export const getCurrentADDate = () => {
  return new Date().toISOString().split('T')[0];
};

/**
 * Validate BS date format
 * @param {string} bsDate - BS date string
 * @returns {boolean} True if valid
 */
export const isValidBSDate = (bsDate) => {
  try {
    const [year, month, day] = bsDate.split('-').map(Number);
    return year >= 2000 && year <= 2100 && month >= 1 && month <= 12 && day >= 1 && day <= 32;
  } catch {
    return false;
  }
};
