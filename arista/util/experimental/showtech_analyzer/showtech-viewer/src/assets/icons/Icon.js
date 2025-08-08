/* 
This file dynamically imports all SVG files in the current
directory and provides a general Icon component that renders 
the appropriate SVG based on the name prop.
*/

// Import all SVG files as React components
import { ReactComponent as FanSVG } from './fan.svg';
import { ReactComponent as PSUSVG } from './psu.svg';
import { ReactComponent as BackArrowSVG } from './back-arrow.svg';
import { ReactComponent as ErrorTriangleSVG } from './error-triangle.svg';
import { ReactComponent as ChevronDownSVG } from './chevron-down.svg';
import { ReactComponent as UploadSVG } from './upload.svg';

// Map of icon names to their SVG components
const iconMap = {
  'fan': FanSVG,
  'psu': PSUSVG,
  'back-arrow': BackArrowSVG,
  'error-triangle': ErrorTriangleSVG,
  'chevron-down': ChevronDownSVG,
  'upload': UploadSVG,
};

// General Icon component that renders the appropriate SVG
const Icon = ({ name, className, style, ...props }) => {
  const SVGComponent = iconMap[name];

  if (!SVGComponent) {
    console.warn(`Icon "${name}" not found. Available icons: ${Object.keys(iconMap).join(', ')}`);
    return null;
  }

  return (
    <SVGComponent
      className={className}
      style={style}
      {...props}
    />
  );
};

// Named exports for convenience
export const FanIcon = (props) => <Icon name="fan" {...props} />;
export const PSUIcon = (props) => <Icon name="psu" {...props} />;
export const BackArrowIcon = (props) => <Icon name="back-arrow" {...props} />;
export const ErrorTriangleIcon = (props) => <Icon name="error-triangle" {...props} />;
export const ChevronDownIcon = (props) => <Icon name="chevron-down" {...props} />;
export const UploadIcon = (props) => <Icon name="upload" {...props} />;

export default Icon;
