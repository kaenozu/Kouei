import React, { useState, useRef, useEffect } from 'react';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';

const DatePicker = ({ value, onChange, label }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [viewDate, setViewDate] = useState(() => {
    if (value) {
      const year = value.substring(0, 4);
      const month = value.substring(4, 6);
      return new Date(parseInt(year), parseInt(month) - 1);
    }
    return new Date();
  });
  const ref = useRef(null);

  // Parse YYYYMMDD to display format
  const formatDisplay = (yyyymmdd) => {
    if (!yyyymmdd || yyyymmdd.length !== 8) return '';
    return `${yyyymmdd.substring(0, 4)}/${yyyymmdd.substring(4, 6)}/${yyyymmdd.substring(6, 8)}`;
  };

  // Format Date to YYYYMMDD
  const formatYYYYMMDD = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}${m}${d}`;
  };

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const daysInMonth = new Date(viewDate.getFullYear(), viewDate.getMonth() + 1, 0).getDate();
  const firstDayOfMonth = new Date(viewDate.getFullYear(), viewDate.getMonth(), 1).getDay();
  
  const days = [];
  for (let i = 0; i < firstDayOfMonth; i++) {
    days.push(null);
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }

  const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
  const dayNames = ['日', '月', '火', '水', '木', '金', '土'];

  const prevMonth = () => {
    setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() - 1));
  };

  const nextMonth = () => {
    setViewDate(new Date(viewDate.getFullYear(), viewDate.getMonth() + 1));
  };

  const selectDate = (day) => {
    const selected = new Date(viewDate.getFullYear(), viewDate.getMonth(), day);
    onChange(formatYYYYMMDD(selected));
    setIsOpen(false);
  };

  const goToToday = () => {
    const today = new Date();
    setViewDate(today);
    onChange(formatYYYYMMDD(today));
    setIsOpen(false);
  };

  const isToday = (day) => {
    const today = new Date();
    return viewDate.getFullYear() === today.getFullYear() &&
           viewDate.getMonth() === today.getMonth() &&
           day === today.getDate();
  };

  const isSelected = (day) => {
    if (!value) return false;
    const selectedDate = formatYYYYMMDD(new Date(viewDate.getFullYear(), viewDate.getMonth(), day));
    return selectedDate === value;
  };

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      {label && (
        <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px', fontWeight: '700' }}>
          {label}
        </label>
      )}
      <div
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 14px',
          background: 'var(--glass-highlight)',
          border: '1px solid var(--glass-border)',
          borderRadius: '10px',
          cursor: 'pointer',
          minWidth: '150px',
        }}
      >
        <Calendar size={18} color="var(--primary)" />
        <span style={{ fontWeight: '600' }}>{formatDisplay(value) || '日付を選択'}</span>
      </div>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            marginTop: '8px',
            padding: '16px',
            background: 'var(--bg-surface)',
            border: '1px solid var(--glass-border)',
            borderRadius: '16px',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.4)',
            zIndex: 1000,
            minWidth: '280px',
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <button onClick={prevMonth} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '8px', color: 'var(--text-main)' }}>
              <ChevronLeft size={20} />
            </button>
            <span style={{ fontWeight: '800', fontSize: '1rem' }}>
              {viewDate.getFullYear()}年 {monthNames[viewDate.getMonth()]}
            </span>
            <button onClick={nextMonth} style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '8px', color: 'var(--text-main)' }}>
              <ChevronRight size={20} />
            </button>
          </div>

          {/* Day names */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px', marginBottom: '8px' }}>
            {dayNames.map((name, i) => (
              <div
                key={name}
                style={{
                  textAlign: 'center',
                  fontSize: '0.75rem',
                  fontWeight: '700',
                  color: i === 0 ? 'var(--error)' : i === 6 ? 'var(--primary)' : 'var(--text-muted)',
                  padding: '4px',
                }}
              >
                {name}
              </div>
            ))}
          </div>

          {/* Days */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: '4px' }}>
            {days.map((day, i) => (
              <div
                key={i}
                onClick={() => day && selectDate(day)}
                style={{
                  aspectRatio: '1',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '8px',
                  cursor: day ? 'pointer' : 'default',
                  background: isSelected(day) ? 'var(--primary)' : isToday(day) ? 'rgba(0, 242, 255, 0.1)' : 'transparent',
                  color: isSelected(day) ? '#000' : day ? 'var(--text-main)' : 'transparent',
                  fontWeight: isSelected(day) || isToday(day) ? '700' : '500',
                  border: isToday(day) && !isSelected(day) ? '1px solid var(--primary)' : 'none',
                  transition: 'all 0.15s',
                }}
                onMouseEnter={(e) => {
                  if (day && !isSelected(day)) {
                    e.target.style.background = 'rgba(255, 255, 255, 0.05)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (day && !isSelected(day) && !isToday(day)) {
                    e.target.style.background = 'transparent';
                  } else if (isToday(day) && !isSelected(day)) {
                    e.target.style.background = 'rgba(0, 242, 255, 0.1)';
                  }
                }}
              >
                {day}
              </div>
            ))}
          </div>

          {/* Today button */}
          <button
            onClick={goToToday}
            style={{
              width: '100%',
              marginTop: '12px',
              padding: '10px',
              background: 'var(--glass-highlight)',
              border: '1px solid var(--primary)',
              borderRadius: '8px',
              color: 'var(--primary)',
              fontWeight: '700',
              cursor: 'pointer',
            }}
          >
            今日
          </button>
        </div>
      )}
    </div>
  );
};

export default DatePicker;
