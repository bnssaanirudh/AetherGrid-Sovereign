"use client";

import { useEffect, useRef } from "react";

export function LiveNetworkGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animationFrameId: number;
    let time = 0;

    const resize = () => {
      const parent = canvas.parentElement;
      if (parent) {
        canvas.width = parent.clientWidth;
        canvas.height = parent.clientHeight;
      }
    };
    
    window.addEventListener('resize', resize);
    resize();

    const labels = [
      { text: "SIGNAL MAP...", angle: -Math.PI / 2 },
      { text: "ENCODING...", angle: 0 },
      { text: "ATTENTION...", angle: Math.PI / 2 },
      { text: "ROUTING...", angle: Math.PI },
      { text: "LATENT FLOW...", angle: -Math.PI * 0.75 }
    ];

    const numNodes = 72; // Number of dots in the circle

    const draw = () => {
      time += 0.002; // Rotation speed
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      const radius = Math.min(centerX, centerY) * 0.7; // Circle radius
      
      // Draw central glow/node
      ctx.beginPath();
      ctx.arc(centerX, centerY, 3, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      
      ctx.shadowBlur = 15;
      ctx.shadowColor = "rgba(255, 255, 255, 0.5)";

      // Draw the connections and nodes
      for (let i = 0; i < numNodes; i++) {
        const baseAngle = (i / numNodes) * Math.PI * 2;
        const currentAngle = baseAngle + time;
        
        const x = centerX + Math.cos(currentAngle) * radius;
        const y = centerY + Math.sin(currentAngle) * radius;
        
        // Draw connection to center with a sweeping curve
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        
        // Control point for quadratic curve to make it look like sweeping lines
        const cpX = centerX + Math.cos(currentAngle - 0.5) * (radius * 0.6);
        const cpY = centerY + Math.sin(currentAngle - 0.5) * (radius * 0.6);
        
        ctx.quadraticCurveTo(cpX, cpY, x, y);
        
        // Modulate opacity for a pulsing effect
        const opacity = 0.15 + 0.1 * Math.sin(time * 5 + i);
        ctx.strokeStyle = `rgba(255, 255, 255, ${opacity})`;
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Draw the outer node dot
        ctx.beginPath();
        ctx.arc(x, y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
      }

      ctx.shadowBlur = 0; // Reset shadow for text

      // Draw labels
      ctx.font = "11px monospace";
      ctx.fillStyle = "#ffffff";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      labels.forEach(label => {
         // Fix the labels in place or rotate them slightly? Let's fix them for readability
         const labelRadius = radius * 1.25;
         const lx = centerX + Math.cos(label.angle) * labelRadius;
         const ly = centerY + Math.sin(label.angle) * labelRadius;
         
         ctx.fillText(label.text, lx, ly);
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="w-full h-full absolute inset-0">
      <canvas 
        ref={canvasRef} 
        className="w-full h-full block"
        style={{ pointerEvents: 'none' }}
      />
    </div>
  );
}
