import React, { useState, useEffect } from 'react';
import { adToBS, bsToAD, formatBSDate, formatADDate } from '../../utils/dateConverter';
import './DateSelector.css';

/**
 * DateSelector Component
 * Allows switching between AD and BS date formats
 */
const DateSelector = ({ value, onChange, label = "Date", required = false }) => {
  const [dateFormat, setDateFormat] = useState('AD'); // 'AD' or 'BS'
  const [adDate, setAdDate] = useState('');
  const [bsDate, setBsDate] = useState('');

  useEffect(() => {
    if (value) {
      setAdDate(value);
      setBsDate(adToBS(value));
    }
  }, [value]);

  const handleADChange = (e) => {
    const newAdDate = e.target.value;
    setAdDate(newAdDate);
    setBsDate(adToBS(newAdDate));
    onChange(newAdDate);
  };

  const handleBSChange = (e) => {
    const newBsDate = e.target.value;
    setBsDate(newBsDate);
    const convertedAdDate = bsToAD(newBsDate);
    setAdDate(convertedAdDate);
    onChange(convertedAdDate);
  };

  const toggleFormat = () => {
    setDateFormat(prev => prev === 'AD' ? 'BS' : 'AD');
  };

  return (
    <div className="date-selector">
      <div className="date-selector-header">
        <label>{label} {required && <span className="required">*</span>}</label>
        <button 
          type="button"
          className="format-toggle"
          onClick={toggleFormat}
          title={`Switch to ${dateFormat === 'AD' ? 'BS' : 'AD'} calendar`}
        >
          {dateFormat === 'AD' ? '🇳🇵 Switch to BS' : '🌍 Switch to AD'}
        </button>
      </div>
      
      {dateFormat === 'AD' ? (
        <div className="date-input-group">
          <input
            type="date"
            value={adDate}
            onChange={handleADChange}
            required={required}
            className="date-input"
          />
          {bsDate && (
            <span className="date-preview">
              BS: {formatBSDate(bsDate)}
            </span>
          )}
        </div>
      ) : (
        <div className="date-input-group">
          <input
            type="text"
            value={bsDate}
            onChange={handleBSChange}
            placeholder="YYYY-MM-DD (BS)"
            required={required}
            className="date-input"
            pattern="\d{4}-\d{2}-\d{2}"
          />
          {adDate && (
            <span className="date-preview">
              AD: {formatADDate(adDate)}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default DateSelector;
