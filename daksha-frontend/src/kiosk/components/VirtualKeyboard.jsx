// import React from 'react';
// import { Delete } from 'lucide-react';

// const ROWS = [
//   ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
//   ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
//   ['SHIFT', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '⌫'],
//   ['123', 'SPACE', '.com', '✓'],
// ];

// const NUM_ROWS = [
//   ['1', '2', '3'],
//   ['4', '5', '6'],
//   ['7', '8', '9'],
//   ['⌫', '0', '✓'],
// ];

// /**
//  * VirtualKeyboard
//  * 
//  * Props:
//  * - onKey: (key: string) => void   — called with each keystroke
//  * - mode: 'alpha' | 'numeric'      — which layout to show (default: 'alpha')
//  * - className: string              — optional wrapper class
//  */
// export default function VirtualKeyboard({ onKey, mode = 'alpha', className = '' }) {
//   const [shifted, setShifted] = React.useState(false);
//   const [numMode, setNumMode] = React.useState(false);

//   const handleKey = (key) => {
//     if (key === 'SHIFT') {
//       setShifted(prev => !prev);
//       return;
//     }
//     if (key === '123') {
//       setNumMode(true);
//       return;
//     }
//     if (key === 'ABC') {
//       setNumMode(false);
//       return;
//     }
//     if (key === 'SPACE') {
//       onKey(' ');
//       return;
//     }
//     if (key === '⌫') {
//       onKey('BACKSPACE');
//       return;
//     }
//     if (key === '✓') {
//       onKey('ENTER');
//       return;
//     }

//     const char = shifted ? key.toUpperCase() : key;
//     onKey(char);
//     if (shifted) setShifted(false); // auto unshift after one capital
//   };

//   // Numeric mode
//   if (mode === 'numeric') {
//     return (
//       <div className={`bg-slate-100 rounded-3xl p-4 ${className}`}>
//         <div className="grid grid-cols-3 gap-3">
//           {['1','2','3','4','5','6','7','8','9','⌫','0','✓'].map(key => {
//             const isConfirm = key === '✓';
//             const isDelete = key === '⌫';
//             return (
//               <button
//                 key={key}
//                 onMouseDown={(e) => { e.preventDefault(); handleKey(key); }}
//                 className={`
//                   h-16 rounded-2xl text-2xl font-bold flex items-center justify-center transition-all active:scale-95 select-none
//                   ${isConfirm ? 'bg-green-600 text-white hover:bg-green-700 col-span-1' : ''}
//                   ${isDelete ? 'bg-slate-200 text-slate-700 hover:bg-slate-300' : ''}
//                   ${!isConfirm && !isDelete ? 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50 shadow-sm' : ''}
//                 `}
//               >
//                 {isDelete ? <Delete className="w-5 h-5" /> : key}
//               </button>
//             );
//           })}
//         </div>
//       </div>
//     );
//   }

//   // Alpha mode
//   const rows = numMode
//     ? [['1','2','3','4','5','6','7','8','9','0'], ['-','/',':',';','(',')','$','&','"'], ['ABC','.',',','?','!','\'','⌫'], ['SPACE','✓']]
//     : ROWS;

//   return (
//     <div className={`bg-slate-100 rounded-3xl p-4 space-y-2 ${className}`}>
//       {rows.map((row, rowIndex) => (
//         <div key={rowIndex} className="flex justify-center gap-1.5">
//           {row.map(key => {
//             const isShift = key === 'SHIFT';
//             const isConfirm = key === '✓';
//             const isDelete = key === '⌫';
//             const isSpace = key === 'SPACE';
//             const isMode = key === '123' || key === 'ABC';
//             const isDotCom = key === '.com';

//             return (
//               <button
//                 key={key}
//                 onMouseDown={(e) => { e.preventDefault(); handleKey(key); }}
//                 className={`
//                   h-14 rounded-xl text-lg font-semibold flex items-center justify-center transition-all active:scale-95 select-none
//                   ${isSpace ? 'flex-1 bg-white border border-slate-200 text-slate-500 hover:bg-slate-50 shadow-sm' : ''}
//                   ${isConfirm ? 'px-6 bg-green-600 text-white hover:bg-green-700 shadow-md' : ''}
//                   ${isDelete ? 'px-4 bg-slate-200 text-slate-700 hover:bg-slate-300' : ''}
//                   ${isShift ? `px-4 shadow-sm ${shifted ? 'bg-primary text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'}` : ''}
//                   ${isMode || isDotCom ? 'px-4 bg-slate-200 text-slate-700 hover:bg-slate-300 text-sm' : ''}
//                   ${!isSpace && !isConfirm && !isDelete && !isShift && !isMode && !isDotCom
//                     ? 'w-10 bg-white text-slate-900 border border-slate-200 hover:bg-slate-50 shadow-sm'
//                     : ''}
//                 `}
//               >
//                 {isDelete ? <Delete className="w-4 h-4" /> :
//                  isSpace ? 'space' :
//                  isShift ? (shifted ? '⬆' : '⇧') :
//                  shifted && key.length === 1 ? key.toUpperCase() : key}
//               </button>
//             );
//           })}
//         </div>
//       ))}
//     </div>
//   );
// }