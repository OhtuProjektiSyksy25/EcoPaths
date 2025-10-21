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
            {s.full_address}
          </li>
          ))}
        </ul>)}
    </div>
  );
};

export default InputContainer
