import React from "react";
import { cn } from "@/lib/utils";

export interface MatchGateBarProps {
  skillPct?: number;
  experiencePct?: number;
  titlePct?: number;
  yearsPct?: number;
  overallScore: number;
  gateThreshold?: number;
  className?: string;
  showDetails?: boolean;
}

export function MatchGateBar({
  skillPct = 0,
  experiencePct = 0,
  titlePct = 0,
  yearsPct = 0,
  overallScore,
  gateThreshold = 75,
  className,
  showDetails = false,
}: MatchGateBarProps) {
  const isPass = overallScore >= gateThreshold;
  
  // Calculate relative widths. If individual components aren't provided but overall is,
  // we can just fill it with a generic color, but MSGC is usually provided.
  const totalProvided = skillPct + experiencePct + titlePct + yearsPct;
  const isProportional = totalProvided > 0;
  
  return (
    <div className={cn("flex flex-col gap-1 w-full", className)}>
      <div className="flex items-center gap-4">
        {/* Bar Container */}
        <div className="relative flex-1 h-2.5 bg-secondary rounded-[4px] overflow-visible">
          {/* Segments */}
          <div className="absolute top-0 left-0 h-full flex rounded-[4px] overflow-hidden" style={{ width: `${overallScore}%` }}>
            {isProportional ? (
              <>
                <div className="h-full bg-[var(--color-seg-skill)]" style={{ width: `${(skillPct / totalProvided) * 100}%` }} title={`Skill: ${skillPct}`} />
                <div className="h-full bg-[var(--color-seg-experience)]" style={{ width: `${(experiencePct / totalProvided) * 100}%` }} title={`Experience: ${experiencePct}`} />
                <div className="h-full bg-[var(--color-seg-title)]" style={{ width: `${(titlePct / totalProvided) * 100}%` }} title={`Title: ${titlePct}`} />
                <div className="h-full bg-[var(--color-seg-years)]" style={{ width: `${(yearsPct / totalProvided) * 100}%` }} title={`Years: ${yearsPct}`} />
              </>
            ) : (
              <div className="h-full bg-[var(--color-seg-skill)] w-full" />
            )}
          </div>
          
          {/* Gate Threshold Line */}
          <div 
            className="absolute top-[-2px] bottom-[-2px] w-[2px] bg-destructive z-10" 
            style={{ left: `${gateThreshold}%` }}
          >
            {/* Diamond cap */}
            <div className="absolute top-[-3px] left-[-3px] w-[8px] h-[8px] bg-destructive rotate-45" />
          </div>
        </div>
        
        {/* Score & Badge Container */}
        <div className="flex flex-col items-end shrink-0 min-w-[48px]">
          <span className="font-mono font-semibold text-foreground text-lg leading-none">
            {overallScore}%
          </span>
          <span 
            className={cn(
              "text-[10px] px-1.5 py-0.5 rounded-sm font-bold mt-1 leading-none uppercase tracking-wider",
              isPass 
                ? "bg-[var(--color-pass-light)] text-[var(--color-pass)]" 
                : "bg-destructive/10 text-destructive"
            )}
          >
            {isPass ? "PASS" : "FLAG"}
          </span>
        </div>
      </div>
      
      {showDetails && isProportional && (
        <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground mt-2">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[var(--color-seg-skill)]"></span> Skill</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[var(--color-seg-experience)]"></span> Experience</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[var(--color-seg-title)]"></span> Title</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-sm bg-[var(--color-seg-years)]"></span> Years</span>
        </div>
      )}
    </div>
  );
}
