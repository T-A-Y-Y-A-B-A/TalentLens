import { Shapes, SquareActivity, CircleDashed } from 'lucide-react';
import { Logo } from '@/components/ui/logo';

interface AuthBrandPanelProps {
  headline: string;
  subtext: string;
}

export function AuthBrandPanel({ headline, subtext }: AuthBrandPanelProps) {
  return (
    <div className="hidden lg:flex lg:w-1/2 relative bg-zinc-950 overflow-hidden items-center justify-center p-12">
      {/* Aesthetic Gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-700 via-indigo-900 to-zinc-950 opacity-90" />
      
      {/* Decorative Symbols */}
      <div className="absolute top-20 right-20 text-indigo-400/20">
        <CircleDashed size={240} strokeWidth={1} />
      </div>
      <div className="absolute bottom-20 left-20 text-indigo-500/20">
        <SquareActivity size={180} strokeWidth={1} />
      </div>
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-white/5">
        <Shapes size={600} strokeWidth={0.5} />
      </div>

      {/* Content */}
      <div className="relative z-10 max-w-lg text-white flex flex-col gap-6">
        <Logo size="lg" showText={false} className="[&_svg]:opacity-80" />
        <h2 className="text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight">
          {headline}
        </h2>
        <p className="text-lg text-indigo-100/80 leading-relaxed font-medium">
          {subtext}
        </p>
      </div>
    </div>
  );
}
