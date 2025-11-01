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
import React, {useState, useEffect, useRef} from "react";

// Keys used by the backend to classify POIs (keep in sync with backend POI_KEYS)
const POI_KEYS: Set<string> = new Set([
  "amenity",
  "tourism",
  "shop",
  "leisure",
  "historic",
  "office",
  "craft",
]);

interface InputContainerProps {
  placeholder: string;
  value: string;
  onChange: (value:string) => void;
  suggestions: any[];
  onSelect: (place: any) => void;
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
  onBlur

  }) => {

const [isOpen, setIsOpen] = useState(false)
const containerRef = useRef<HTMLDivElement | null>(null);
const inputSelected = useRef(false);

// Prepare suggestions so that POIs are shown after address suggestions
const prepareSuggestions = (items: any[]) => {
  if (!items || items.length === 0) return items;
  const isPoi = (suggestion: any) => !!suggestion?.properties?.osm_key && POI_KEYS.has(suggestion.properties.osm_key);
  // stable-ish sort: copy the array and sort by isPoi (false first)
  return [...items].sort((a, b) => {
    const aPoi = isPoi(a);
    const bPoi = isPoi(b);
    if (aPoi === bPoi) return 0;
    return aPoi ? 1 : -1;
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

  (!suggestions || suggestions == undefined || suggestions.length === 0) ? setIsOpen(false) : setIsOpen(true)

},[suggestions])


useEffect(() => {
  /*
  useEffect for handling clicks outside of input / suggestions box to update isOpen useState
  */
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);


 return (
    <div className="InputContainer" ref={containerRef}>
      <input
      type="text"
      value={value}
      onChange={(e)=> onChange(e.target.value)}
      placeholder={placeholder}
      onFocus={() => {
        suggestions.length > 0 && inputSelected.current === false && setIsOpen(true);
        onFocus?.();
      }}
      onBlur={() => {
        onBlur?.();
      }}
			/>
      {isOpen && suggestions?.length && (
        <ul className="originul">
        {suggestions.map((s, i) => (
          <li 
          className="originli" 
          key={`${s.properties.osm_id}-${i}`}
          onClick={() => {
            onChange(s.full_address)
            if (onSelect) onSelect(s)
            setIsOpen(false)
            inputSelected.current = true;
          }}>
            {/* POI icon: render a small marker when the suggestion is classified as a POI */}
            {s?.properties?.osm_key && POI_KEYS.has(s.properties.osm_key) && (
              <span className="poi-icon" aria-hidden="true" title="Point of interest" style={{display: 'inline-block', verticalAlign: 'middle', marginRight: 8}}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="#d33"/>
                  <circle cx="12" cy="9" r="2.5" fill="#fff"/>
                </svg>
              </span>
            )}
            {s.full_address}
          </li>
          ))}
        </ul>)}
    </div>
  );
};

export default InputContainer
