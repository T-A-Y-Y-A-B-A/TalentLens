import { Shapes, SquareActivity, CircleDashed } from 'lucide-react';
import { Logo } from '@/components/ui/logo';
import { AuthBrandPanel } from '@/components/AuthBrandPanel';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen w-full bg-white">
      {/* Left side: Form */}
      <div className="flex flex-1 flex-col px-4 py-12 sm:px-6 lg:flex-none lg:w-1/2 lg:px-20 xl:px-24 justify-center">
        <div className="mx-auto w-full max-w-sm lg:max-w-md relative flex flex-col justify-center min-h-[500px]">
          <div className="absolute top-0 left-0">
            <Logo href="/" size="md" />
          </div>
          <div className="mt-20 w-full">
            {children}
          </div>
        </div>
      </div>

      <AuthBrandPanel 
        headline="Discover the right talent, effortlessly."
        subtext="Join thousands of organizations building world-class teams with data-driven insights and an unparalleled candidate experience."
      />
    </div>
  );
}
