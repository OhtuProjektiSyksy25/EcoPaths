/*
Component that renders a single input field
Props:
	-placeholder: string shown when no input has been given (string)
	-value: current input value (string)
	-onChange: callback function called with updated value on value change
*/
import React, {useState, useEffect, useRef} from "react";


interface InputContainerProps {
  placeholder: string;
  value: string;
  onChange: (value:string) => void;
  suggestions: any[];
  onSelect: (place: any) => void;
}

const InputContainer: React.FC<InputContainerProps> = ({
  placeholder,
  value,
  onChange,
  suggestions,
  onSelect
  
  }) => {

const [isOpen, setIsOpen] = useState(false)
const containerRef = useRef<HTMLDivElement | null>(null);

useEffect(() => {
(!suggestions || suggestions == undefined || suggestions.length === 0) ? setIsOpen(false) : setIsOpen(true)

},[suggestions])


useEffect(() => {
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
      onFocus={() => suggestions.length > 0 && setIsOpen(true)}
			/>
      {isOpen && suggestions?.length && (
        <ul className="originul">
        {suggestions.map((s) => (
          <li 
          className="originli" 
          key={s.properties.osm_id}
          onClick={() => {
            onChange(s.full_address)
            if (onSelect) onSelect(s)
            setIsOpen(false)
          }}>
            {s.full_address}
          </li>
          ))}
        </ul>)}
    </div>
  );
};

export default InputContainer
