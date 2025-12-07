/*
Component that renders a single input field
Props:
	-placeholder: string shown when no input has been given (string)
	-value: current input value (string)
	-onChange: callback function called with updated value on value change
  -suggestoins: list of address suggestions
  -onSelect: callback function called with chosen suggestion
  -onFocus: optional callback when input is focused
  -onBlur: optional callback when input loses focus
*/
import React, { useState, useEffect, useRef } from 'react';
import { ReactComponent as PoiIcon } from '../assets/icons/poi-icon.svg';
import { X } from 'lucide-react';
import { Place } from '../types';

// Keys used by the backend to classify POIs (keep in sync with backend POI_KEYS)
const POI_KEYS: Set<string> = new Set([
  'amenity',
  'tourism',
  'shop',
  'leisure',
  'historic',
  'office',
  'craft',
]);

interface InputContainerProps {
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  suggestions: Place[];
  onSelect: (place: Place) => void;
  onFocus?: () => void;
  onBlur?: () => void;
}

const InputContainer: React.FC<InputContainerProps> = ({
  placeholder,
  value,
  onChange,
  suggestions,
  onSelect,
  onFocus,
  onBlur,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const inputSelected = useRef(false);

  // Prepare suggestions so that POIs are shown after address suggestions
  const prepareSuggestions = (items: Place[]): Place[] => {
    if (!items || items.length === 0) return items;
    const isPoi = (suggestion: Place): boolean =>
      !!suggestion?.properties?.osm_key && POI_KEYS.has(suggestion.properties.osm_key);
    // stable-ish sort: copy the array and sort by isPoi (POIs first)
    // keep original relative ordering among POIs and among addresses
    return [...items].sort((a, b) => {
      const aPoi = isPoi(a);
      const bPoi = isPoi(b);
      if (aPoi === bPoi) return 0;
      // if a is a POI and b is not, a should come first (-1)
      return aPoi ? -1 : 1;
    });
  };

  const sortedSuggestions = prepareSuggestions(suggestions);

  useEffect(() => {
    /*
  useEffect for updating isOpen useState when suggestion updates
  */
    if (inputSelected.current) {
      inputSelected.current = false;
      setIsOpen(false);
      return;
    }

    !suggestions || suggestions === undefined || suggestions.length === 0
      ? setIsOpen(false)
      : setIsOpen(true);
  }, [suggestions]);

  useEffect(() => {
    /*
  useEffect for handling clicks outside of input / suggestions box to update isOpen useState
  */
    const handleClickOutside = (event: MouseEvent): void => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const isMobile = window.innerWidth <= 800;

  return (
    <div className='InputContainer' ref={containerRef}>
      <input
        ref={inputRef}
        type='text'
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        onFocus={() => {
          suggestions?.length > 0 && inputSelected.current === false && setIsOpen(true);
          onFocus?.();
          if (!isMobile && value) {
            inputRef.current?.select();
          }
        }}
        onBlur={() => {
          onBlur?.();
        }}
      />
      {isMobile && value && (
        <button
          className='clear-button'
          onClick={() => {
            onChange('');
            inputRef.current?.focus();
          }}
          type='button'
        >
          <X size={18} />
        </button>
      )}
      {isOpen && sortedSuggestions?.length && (
        <ul className='originul'>
          {sortedSuggestions.map((s, i) => (
            <li
              className='originli'
              key={`${s.properties?.osm_id || i}`}
              onClick={() => {
                inputSelected.current = true;
                onChange(s.full_address);
                if (onSelect) onSelect(s);
                setIsOpen(false);
              }}
            >
              {/* POI icon: render a small marker when the suggestion is classified as a POI */}
              {s?.properties?.osm_key && POI_KEYS.has(s.properties.osm_key) && (
                <PoiIcon
                  aria-hidden='true'
                  style={{
                    width: 14,
                    height: 14,
                    verticalAlign: 'middle',
                    marginRight: 8,
                    color: '#d33',
                  }}
                />
              )}
              {s.full_address}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default InputContainer;
