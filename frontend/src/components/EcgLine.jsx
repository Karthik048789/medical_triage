import { useEffect, useRef } from "react";

const ECG_PATH =
  "M0,30 L20,30 L25,10 L30,50 L35,5 L40,55 L45,30 L80,30 L85,10 L90,50 L95,5 L100,55 L105,30 L150,30";

export default function EcgLine({ color = "#00ffe0", width = 150, height = 60, speed = 2 }) {
  const pathRef = useRef(null);

  useEffect(() => {
    const path = pathRef.current;
    if (!path) return;
    const len = path.getTotalLength();
    path.style.strokeDasharray = len;
    path.style.strokeDashoffset = len;

    let start = null;
    let raf;
    const duration = 1800 / speed;

    function animate(ts) {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      path.style.strokeDashoffset = len * (1 - progress);
      if (progress < 1) {
        raf = requestAnimationFrame(animate);
      } else {
        setTimeout(() => {
          start = null;
          path.style.strokeDashoffset = len;
          raf = requestAnimationFrame(animate);
        }, 400);
      }
    }

    raf = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(raf);
  }, [speed]);

  return (
    <svg width={width} height={height} viewBox={`0 0 150 60`} style={{ overflow: "visible" }}>
      <path
        d={ECG_PATH}
        fill="none"
        stroke={color}
        strokeWidth="2"
        ref={pathRef}
        style={{
          filter: `drop-shadow(0 0 4px ${color}) drop-shadow(0 0 10px ${color})`,
        }}
      />
    </svg>
  );
}
