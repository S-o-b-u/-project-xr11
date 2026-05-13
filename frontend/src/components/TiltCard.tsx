"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { ReactNode, useState } from "react";

export function TiltCard({ children, className = "" }: { children: ReactNode; className?: string }) {
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const shineX = useMotionValue(0);
  const shineY = useMotionValue(0);

  const [isHovered, setIsHovered] = useState(false);

  const mouseXSpring = useSpring(x, { stiffness: 300, damping: 30 });
  const mouseYSpring = useSpring(y, { stiffness: 300, damping: 30 });

  const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ["10deg", "-10deg"]);
  const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ["-10deg", "10deg"]);

  const shineBg = useTransform(
    [shineX, shineY],
    ([sx, sy]) => `radial-gradient(circle at ${sx}px ${sy}px, rgba(255,61,0,0.06) 0%, transparent 60%)`
  );

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    x.set(e.clientX / rect.width - 0.5 - rect.left / rect.width + 0.5);
    y.set(e.clientY / rect.height - 0.5 - rect.top / rect.height + 0.5);
    
    const localX = e.clientX - rect.left;
    const localY = e.clientY - rect.top;
    x.set(localX / rect.width - 0.5);
    y.set(localY / rect.height - 0.5);
    shineX.set(localX);
    shineY.set(localY);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    x.set(0);
    y.set(0);
  };

  return (
    <div style={{ perspective: "800px" }} className="h-full w-full">
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: "preserve-3d",
        }}
        initial="initial"
        whileHover="hover"
        variants={{
          initial: { scale: 1 },
          hover: { scale: 1.015, transition: { duration: 0.25 } },
        }}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onMouseEnter={() => setIsHovered(true)}
        className={`relative w-full h-full rounded-2xl border border-white/[0.06] bg-[#0A0A0A] p-8 transition-all duration-300 hover:border-white/[0.1] hover:shadow-[0_0_60px_rgba(255,61,0,0.03)] ${className}`}
      >
        {/* Red glow shine on hover */}
        <div className="pointer-events-none absolute inset-0 rounded-2xl overflow-hidden">
          <motion.div
            className="absolute inset-0"
            style={{
              background: shineBg,
              opacity: isHovered ? 1 : 0,
            }}
            transition={{ duration: 0.3 }}
          />
        </div>
        <div style={{ transform: "translateZ(30px)", transformStyle: "preserve-3d" }} className="h-full w-full flex flex-col justify-between relative z-10">
          {children}
        </div>
      </motion.div>
    </div>
  );
}
