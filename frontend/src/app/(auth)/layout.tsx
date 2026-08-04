import Link from 'next/link';
import { Hexagon, Shapes, SquareActivity, CircleDashed } from 'lucide-react';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-white">
      {/* Left side: Form */}
      <div className="flex flex-1 flex-col px-4 py-12 sm:px-6 lg:flex-none lg:w-1/2 lg:px-20 xl:px-24 justify-center">
        <div className="mx-auto w-full max-w-sm lg:max-w-md relative flex flex-col justify-center min-h-[500px]">
          <Link href="/" className="absolute top-0 left-0 flex items-center gap-2 font-bold text-xl text-zinc-900 hover:text-zinc-700 transition-colors">
            <Hexagon className="h-6 w-6 text-indigo-600 fill-indigo-600" />
            <span>TalentLens</span>
          </Link>
          <div className="mt-20 w-full">
            {children}
          </div>
        </div>
      </div>

      {/* Right side: Branded panel */}
      <div className="hidden lg:flex lg:flex-1 relative bg-zinc-950 overflow-hidden items-center justify-center p-12">
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
          <Hexagon className="h-12 w-12 text-indigo-400 fill-indigo-400 mb-2" />
          <h2 className="text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight">
            Discover the right talent, effortlessly.
          </h2>
          <p className="text-lg text-indigo-100/80 leading-relaxed font-medium">
            Join thousands of organizations building world-class teams with data-driven insights and an unparalleled candidate experience.
          </p>
        </div>
      </div>
    </div>
  );
}
