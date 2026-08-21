'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { 
  Menu, 
  PlayCircle, 
  Sparkles, 
  Search, 
  BotMessageSquare, 
  ShieldCheck, 
  ArrowRight, 
  BrainCircuit, 
  X, 
  UserCircle2, 
  Quote
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Logo } from '@/components/ui/logo';

function Navbar() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Product', href: '#product' },
    { name: 'How it Works', href: '#how-it-works' },
    { name: 'Pricing', href: '#pricing' },
    { name: 'For Candidates', href: '/portal/login' },
  ];

  return (
    <header
      className={`fixed top-0 w-full z-50 transition-all duration-300 ${
        scrolled ? 'bg-white shadow-sm border-b border-zinc-100 py-3' : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        <Logo href="/" size="md" />

        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.name}
              href={link.href}
              className="text-sm font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
            >
              {link.name}
            </Link>
          ))}
        </nav>

        <div className="hidden md:flex items-center gap-4">
          <Link href="/login">
            <Button variant="ghost" className="font-semibold rounded-xl">HR Sign In</Button>
          </Link>
          <Link href="/portal/login">
            <Button className="bg-[var(--signal)] hover:bg-[var(--signal)]/90 text-white rounded-xl font-semibold">
              Get Started as Candidate
            </Button>
          </Link>
        </div>

        <div className="md:hidden">
          <Sheet>
            <SheetTrigger render={<Button variant="ghost" size="icon" aria-label="Open menu" />}>
              <Menu className="h-6 w-6 text-zinc-900" />
            </SheetTrigger>
            <SheetContent side="right" className="bg-white p-6">
               <SheetTitle className="sr-only">Navigation Menu</SheetTitle>
              <Logo href="/" size="md" className="mb-8 mt-4" />
              <nav className="flex flex-col gap-6">
                {navLinks.map((link) => (
                  <Link
                    key={link.name}
                    href={link.href}
                    className="text-lg font-medium text-zinc-600 hover:text-zinc-900 transition-colors"
                  >
                    {link.name}
                  </Link>
                ))}
                <div className="flex flex-col gap-4 mt-4">
                  <Link href="/login" className="w-full">
                    <Button variant="outline" className="w-full justify-center rounded-xl font-semibold h-12">
                      HR Sign In
                    </Button>
                  </Link>
                  <Link href="/portal/login" className="w-full">
                    <Button className="w-full bg-[var(--signal)] hover:bg-[var(--signal)]/90 text-white justify-center rounded-xl font-semibold h-12">
                      Get Started as Candidate
                    </Button>
                  </Link>
                </div>
              </nav>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-indigo-50 rounded-full blur-3xl opacity-50 -z-10" />

      <div className="max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
        <div className="flex flex-col gap-8 max-w-2xl text-center lg:text-left">
          <h1 className="text-5xl lg:text-6xl font-bold tracking-tight text-zinc-900 leading-[1.1]">
            Uncover hidden potential.<br />
            <span className="text-indigo-600">Hire the perfect fit, every time.</span>
          </h1>
          
          <p className="text-lg lg:text-xl text-zinc-600 leading-relaxed">
            Powered by vector embeddings, hybrid semantic search, and LLM reasoning to match candidates with unprecedented precision.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
            <Link href="/portal/login" className="w-full sm:w-auto">
              <Button size="lg" className="bg-[var(--signal)] hover:bg-[var(--signal)]/90 text-white rounded-xl font-semibold h-12 px-8 w-full">
                Get Started as Candidate
              </Button>
            </Link>

            <Dialog>
              <DialogTrigger render={<Button variant="outline" size="lg" className="rounded-xl font-semibold h-12 px-8 w-full sm:w-auto border-zinc-200 hover:bg-zinc-50 hover:text-indigo-600" />}>
                <PlayCircle className="mr-2 h-5 w-5" />
                Watch Demo
              </DialogTrigger>
              <DialogContent className="sm:max-w-2xl p-0 overflow-hidden bg-zinc-950 border-none rounded-2xl">
                <DialogHeader className="sr-only">
                  <DialogTitle>Product Demo</DialogTitle>
                  <DialogDescription>A short video demonstrating TalentLens capabilities.</DialogDescription>
                </DialogHeader>
                <div className="aspect-video w-full flex flex-col items-center justify-center text-zinc-500 bg-zinc-900">
                  <PlayCircle className="h-16 w-16 text-zinc-700 mb-4" />
                  <p className="font-medium">Video Player Placeholder</p>
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Hero illustration — replaces the old candidate card mockup */}
        <div className="relative w-full max-w-lg mx-auto flex items-center justify-center">
          {/* Soft indigo glow for visual depth, matching the old card's shadow treatment */}
          <div className="absolute -inset-6 bg-gradient-to-tr from-indigo-100 to-white opacity-60 rounded-3xl blur-2xl -z-10" />
          {/* Plain <img> intentionally — next/image strips GIF animation frames */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/hero-Illustration.gif"
            alt="TalentLens hiring platform illustration"
            className="w-full max-w-lg h-auto object-contain drop-shadow-xl"
          />
        </div>
      </div>
    </section>
  );
}

function TrustStrip() {
  const logos = [
    { src: '/logos/abc.jpg',         alt: 'ABC logo',         w: 180, containerW: 'w-44' },
    { src: '/logos/xyz.jpg',         alt: 'XYZ logo',         w: 135, containerW: 'w-32' },
    { src: '/logos/digitalsoft.jpg', alt: 'DigitalSoft logo', w: 200, containerW: 'w-48' },
    { src: '/logos/tw.jpg',          alt: 'TW logo',          w: 160, containerW: 'w-40' },
  ];

  return (
    <div className="border-y border-zinc-100 bg-white py-10">
      <div className="max-w-7xl mx-auto px-6">
        <p className="text-center text-sm font-bold text-zinc-400 uppercase tracking-widest mb-8">
          Built for recruiting teams that move fast
        </p>
        {/* overflow-hidden clips the duplicate set — do not remove */}
        <div className="overflow-hidden w-full">
          {/*
            animate-marquee scrolls the flex row from 0 → -50%.
            Because the list is rendered TWICE back-to-back, the total width
            is 2×, so -50% lands exactly back at the start — no visible jump.
            ⚠ If you change the number of logos or gap, keep the list doubled
              and keep the keyframe target at -50%.
          */}
          <div className="flex animate-marquee w-max items-center gap-16">
            {[...logos, ...logos].map((logo, i) => (
              <div
                key={i}
                className={`flex items-center justify-center ${logo.containerW} h-16 shrink-0`}
              >
                <Image
                  src={logo.src}
                  alt={logo.alt}
                  width={logo.w}
                  height={44}
                  className="max-h-11 w-auto object-contain grayscale opacity-70 hover:opacity-100 hover:grayscale-0 transition duration-200"
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}


function WhyTalentLens() {
  const features = [
    {
      icon: Search,
      title: 'AI Resume Matching',
      description:
        'Go beyond keyword matching. Our semantic hybrid search understands context and reranks candidates for true relevance.',
    },
    {
      icon: BotMessageSquare,
      title: 'Recruiter Copilot',
      description:
        'Search candidates using natural language. We show you the exact interpreted filters—no opaque AI-generated SQL—so you stay in control.',
    },
    {
      icon: ShieldCheck,
      title: 'Multi-Tenant by Design',
      description:
        'Built for scale with strict org-isolated data environments, comprehensive role-based access control, and complete audit trails.',
    },
  ];

  return (
    <section id="how-it-works" className="py-20 lg:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl lg:text-4xl font-bold tracking-tight text-zinc-900 mb-4">
            A smarter way to build your team
          </h2>
          <p className="text-lg text-zinc-600">
            We&#39;ve replaced broken keyword searches with an intelligent architecture designed to understand both the role and the candidate.
          </p>
        </div>

        {/* Section-level illustration: sits above the 3 feature cards */}
        <div className="grid md:grid-cols-2 gap-10 lg:gap-16 items-center mb-20">
          <div className="space-y-4 text-zinc-600 text-lg font-medium leading-relaxed">
            <p>Our AI doesn&#39;t just search — it <strong className="text-zinc-900">understands</strong>. Every resume is converted into rich vector embeddings that capture the true depth of a candidate&#39;s background.</p>
            <p>Combine that with hybrid BM25 + semantic search and LLM-powered reasoning and you get matches that keyword filters will always miss.</p>
          </div>
          <div className="flex justify-center md:justify-end">
            <Image
              src="/illustrations/resume-matching.png"
              alt="AI resume matching and candidate review"
              width={480}
              height={480}
              className="w-full max-w-sm h-auto object-contain drop-shadow-md"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-10 lg:gap-16">
          {features.map((feature, idx) => (
            <div key={idx} className="flex flex-col items-center md:items-start text-center md:text-left">
              <div className="w-14 h-14 rounded-2xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-6">
                <feature.icon size={28} strokeWidth={2} />
              </div>
              <h3 className="text-xl font-bold text-zinc-900 mb-3">{feature.title}</h3>
              <p className="text-zinc-600 leading-relaxed font-medium">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ProductShowcase() {
  return (
    <section id="product" className="py-20 lg:py-32 bg-zinc-50 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 space-y-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div className="order-2 lg:order-1 relative">
            <div className="bg-white shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-zinc-100 rounded-xl p-8 space-y-6">
              <div className="flex items-center justify-between pb-2">
                <h4 className="font-bold text-zinc-900 font-serif text-lg">Ranked Candidates</h4>
                <span className="text-sm text-zinc-500 font-serif">42 matches</span>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-5 p-5 rounded-xl border border-indigo-100 bg-[#F9FAFF]">
                <div className="w-10 h-10 rounded-full bg-indigo-100/80 flex items-center justify-center text-indigo-700 font-bold shrink-0 font-serif">1</div>
                <div className="flex-1 space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-bold text-zinc-900 font-serif text-lg">Sarah Jenkins</p>
                      <p className="text-[15px] text-zinc-500 font-serif">Staff Engineer</p>
                    </div>
                    <div className="bg-indigo-100/50 text-indigo-700 px-3 py-1 rounded-md text-xs font-bold flex items-center gap-1">
                      <Sparkles size={12} /> 98%
                    </div>
                  </div>
                  <p className="text-[15px] text-zinc-700 font-serif"><strong className="font-bold">Strength:</strong> 5+ years building distributed Go systems.</p>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-5 p-5 rounded-xl border border-zinc-100 bg-white">
                <div className="w-10 h-10 rounded-full bg-zinc-100 flex items-center justify-center text-zinc-500 font-bold shrink-0 font-serif">2</div>
                <div className="flex-1 space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-bold text-zinc-900 font-serif text-lg">Marcus Chen</p>
                      <p className="text-[15px] text-zinc-500 font-serif">Backend Dev</p>
                    </div>
                    <div className="text-zinc-500 px-3 py-1 text-xs font-bold font-serif">
                      91%
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-[11px] uppercase font-bold text-red-500 bg-red-50/50 px-2 py-0.5 rounded font-sans tracking-wide">Missing: Kubernetes</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="order-1 lg:order-2 space-y-8 pl-4">
            <h3 className="text-3xl lg:text-4xl font-bold text-zinc-900 tracking-tight font-serif">
              Precision matching, fully explained.
            </h3>
            <div className="space-y-6 text-lg text-zinc-600 font-serif leading-relaxed">
              <p>We convert every resume into deep vector embeddings to understand the true context of a candidate&#39;s experience.</p>
              <p>Next, a hybrid search algorithm combines semantic meaning with hard filters to surface the most relevant talent.</p>
              <p>Finally, we rerank the top results and generate a clear, LLM-powered explanation of exactly why a candidate fits—and what they might be missing.</p>
            </div>
            <div className="flex justify-start">
              <Image
                src="/illustrations/analytics-growth.png"
                alt="Analytics and matching growth chart"
                width={400}
                height={320}
                className="w-full max-w-xs h-auto object-contain drop-shadow-sm"
              />
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div className="order-1 space-y-6">
            <h3 className="text-3xl lg:text-4xl font-bold text-zinc-900 tracking-tight">
              A pipeline that moves with you.
            </h3>
            <div className="space-y-4 text-lg text-zinc-600 font-medium">
              <p>Manage your entire hiring flow visually with intuitive drag-and-drop stages.</p>
              <p>Move candidates from Screening to Interview to Offer effortlessly. Every state change is logged, giving you a complete history and full audit trail of the hiring process.</p>
            </div>
          </div>
          
          <div className="order-2 relative overflow-hidden rounded-2xl border border-zinc-200 shadow-xl bg-white p-4">
             <div className="flex gap-4 min-w-[600px] overflow-hidden">
                <div className="w-1/3 bg-zinc-50 rounded-xl p-3 space-y-3 border border-zinc-100">
                  <div className="flex items-center justify-between px-1">
                    <p className="text-sm font-bold text-zinc-700 uppercase tracking-wide">Screening</p>
                    <span className="bg-zinc-200 text-zinc-600 text-xs px-2 py-0.5 rounded-full font-bold">1</span>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm border border-zinc-200 space-y-2 cursor-grab active:cursor-grabbing hover:border-indigo-300 transition-colors">
                    <p className="font-bold text-zinc-900 text-sm">Elena Rust</p>
                    <p className="text-xs text-zinc-500">Product Designer</p>
                  </div>
                </div>

                <div className="w-1/3 bg-indigo-50/30 rounded-xl p-3 space-y-3 border border-indigo-100/50">
                  <div className="flex items-center justify-between px-1">
                    <p className="text-sm font-bold text-indigo-700 uppercase tracking-wide">Interview</p>
                    <span className="bg-indigo-100 text-indigo-700 text-xs px-2 py-0.5 rounded-full font-bold">2</span>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm border border-zinc-200 space-y-2 cursor-grab transform rotate-1 border-indigo-400 relative z-10 scale-105 shadow-md">
                    <p className="font-bold text-zinc-900 text-sm">Marcus Chen</p>
                    <p className="text-xs text-zinc-500">Backend Dev</p>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm border border-zinc-200 space-y-2 cursor-grab opacity-70">
                    <p className="font-bold text-zinc-900 text-sm">David Kim</p>
                    <p className="text-xs text-zinc-500">DevOps Engineer</p>
                  </div>
                </div>

                <div className="w-1/3 bg-zinc-50 rounded-xl p-3 space-y-3 border border-zinc-100">
                  <div className="flex items-center justify-between px-1">
                    <p className="text-sm font-bold text-zinc-700 uppercase tracking-wide">Offer</p>
                    <span className="bg-zinc-200 text-zinc-600 text-xs px-2 py-0.5 rounded-full font-bold">0</span>
                  </div>
                  <div className="border-2 border-dashed border-zinc-200 rounded-lg h-24 flex items-center justify-center">
                    <p className="text-xs text-zinc-400 font-medium">Drop candidate here</p>
                  </div>
                </div>
             </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          <div className="order-2 lg:order-1 relative">
            <div className="absolute inset-0 bg-indigo-100/50 rounded-3xl blur-2xl -z-10 transform translate-y-4"></div>
            <div className="bg-white border border-zinc-200 shadow-xl rounded-2xl p-6 sm:p-8 space-y-6">
              
              <div className="space-y-2">
                <label className="text-sm font-bold text-zinc-700 flex items-center gap-2">
                  <BrainCircuit size={16} className="text-indigo-600" /> Ask the Copilot
                </label>
                <div className="relative">
                  <input 
                    type="text" 
                    value="Python developers, 3+ years, AWS"
                    readOnly
                    className="w-full bg-zinc-50 border border-zinc-200 rounded-xl py-3 px-4 text-zinc-900 font-medium focus:outline-none"
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 bg-indigo-600 rounded-lg w-8 h-8 flex items-center justify-center text-white">
                    <ArrowRight size={16} />
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-zinc-100 space-y-3">
                <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Interpreted Filters</p>
                <div className="flex flex-wrap gap-2">
                  <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                    Skill: Python <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                  </div>
                  <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                    Experience &ge; 3 yrs <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                  </div>
                  <div className="bg-indigo-50 border border-indigo-100 text-indigo-700 px-3 py-1.5 rounded-lg text-sm font-semibold flex items-center gap-2">
                    Skill: AWS <X size={14} className="text-indigo-400 hover:text-indigo-700 cursor-pointer" />
                  </div>
                </div>
              </div>

            </div>
          </div>
          
          <div className="order-1 lg:order-2 space-y-6">
            <h3 className="text-3xl lg:text-4xl font-bold text-zinc-900 tracking-tight">
              Human-in-the-loop transparency.
            </h3>
            <div className="space-y-4 text-lg text-zinc-600 font-medium">
              <p>Type what you're looking for naturally. Our AI instantly translates your intent into structured queries.</p>
              <p>We strongly believe in transparency. You always see the exact interpreted filters—no hidden black-box logic, no opaque AI-generated SQL.</p>
              <p>Edit, remove, or adjust the chips to refine your search, keeping you in the driver's seat at all times.</p>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
}

function StatsBand() {
  const stats = [
    {
      value: '<50ms',
      label: 'Search query latency',
    },
    {
      value: '100%',
      label: 'Human-in-the-loop by design',
    },
    {
      value: 'Vector+BM25',
      label: 'Hybrid search & reranking',
    },
    {
      value: 'Complete',
      label: 'Audit trail on every state change',
    },
  ];

  return (
    <section className="bg-zinc-950 py-20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-10 lg:gap-8 divide-y divide-zinc-800/50 lg:divide-y-0 lg:divide-x lg:divide-zinc-800/50">
          {stats.map((stat, idx) => (
            <div key={idx} className={`flex flex-col items-center text-center ${idx > 1 ? 'pt-10 lg:pt-0' : ''}`}>
              <div className="text-3xl lg:text-4xl font-extrabold text-white mb-2 tracking-tight">
                {stat.value}
              </div>
              <div className="text-sm lg:text-base font-semibold text-indigo-400">
                {stat.label}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Testimonials() {
  const testimonials = [
    {
      quote: "TalentLens fundamentally changed how we evaluate engineering talent. We've cut our screening time by 60% while dramatically improving the quality of our on-site interviews.",
      name: "Sarah Chen",
      role: "VP of Engineering",
      company: "TechFlow"
    },
    {
      quote: "The recruiter copilot is a game changer. Being able to just ask for 'someone who can migrate our backend to Go' and actually getting a ranked, reasoned list is incredible.",
      name: "Michael Rodriguez",
      role: "Head of Talent",
      company: "Scale Systems"
    },
    {
      quote: "Finally, an AI tool that explains its work. The transparency of the interpreted filters means my team actually trusts the results instead of second-guessing them.",
      name: "Emily Watson",
      role: "Director of Recruiting",
      company: "FinData Corp"
    }
  ];

  return (
    <section className="py-20 lg:py-32 bg-white">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-3xl lg:text-4xl font-bold tracking-tight text-zinc-900">
            Trusted by modern recruiting teams
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, idx) => (
            <div key={idx} className="bg-zinc-50 rounded-2xl p-8 border border-zinc-100 flex flex-col justify-between">
              <div>
                <Quote className="h-8 w-8 text-indigo-200 mb-6" />
                <p className="text-zinc-700 leading-relaxed font-medium mb-8">
                  "{testimonial.quote}"
                </p>
              </div>
              <div className="flex items-center gap-4">
                <UserCircle2 className="h-12 w-12 text-zinc-400 stroke-[1.5]" />
                <div>
                  <p className="font-bold text-zinc-900">{testimonial.name}</p>
                  <p className="text-sm text-zinc-500">{testimonial.role}, {testimonial.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FinalCTA() {
  return (
    <section className="py-24 bg-white px-6">
      <div className="bg-[#EEF0FD] rounded-3xl px-8 py-16 md:py-20 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-12 items-center max-w-6xl mx-auto">
          {/* LEFT: existing content */}
          <div className="text-center md:text-left">
            <h2 className="text-4xl md:text-5xl font-serif font-bold text-zinc-900">
              Ready to hire smarter?
            </h2>
            <p className="mt-4 text-lg text-zinc-600 font-medium">
              Join the next generation of recruiting teams using TalentLens to uncover hidden potential and move faster than the competition.
            </p>
            <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
              <Link href="/portal/login" className="w-full sm:w-auto">
                <Button size="lg" className="bg-[var(--signal)] hover:bg-[var(--signal)]/90 text-white rounded-xl font-bold h-14 px-10 w-full">
                  Get Started as Candidate
                </Button>
              </Link>
              <Link href="/login" className="w-full sm:w-auto">
                <Button variant="outline" size="lg" className="rounded-xl font-bold h-14 px-10 w-full border-zinc-300 text-zinc-700 hover:bg-zinc-100 bg-white">
                  HR Sign In
                </Button>
              </Link>
            </div>
          </div>

          {/* RIGHT: new video */}
          <div className="rounded-2xl overflow-hidden shadow-xl">
            <video
              src="/videos/product-demo.mp4"
              autoPlay
              muted
              loop
              playsInline
              poster="/videos/product-demo-poster.jpg"
              className="w-full h-auto object-cover rounded-2xl"
            />
          </div>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="bg-white border-t border-zinc-200 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between gap-12 mb-16">
          <div className="md:w-1/3">
            <Logo href="/" size="md" className="mb-4" />
            <p className="text-zinc-500 font-medium leading-relaxed max-w-sm">
              The AI-native recruiting platform built for teams that move fast and hire smart.
            </p>
          </div>

          <div className="md:w-2/3 grid grid-cols-2 sm:grid-cols-3 gap-8">
            <div>
              <h4 className="font-bold text-zinc-900 mb-4">Product</h4>
              <ul className="space-y-3">
                <li><Link href="#features" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Features</Link></li>
                <li><Link href="#pricing" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Pricing</Link></li>
                <li><Link href="/login" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">HR Sign In</Link></li>
                <li><Link href="/portal/login" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Candidate Portal</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-zinc-900 mb-4">Company</h4>
              <ul className="space-y-3">
                <li><Link href="#about" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">About Us</Link></li>
                <li><Link href="#careers" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Careers</Link></li>
                <li><Link href="#contact" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Contact</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-bold text-zinc-900 mb-4">Legal</h4>
              <ul className="space-y-3">
                <li><Link href="#privacy" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Privacy Policy</Link></li>
                <li><Link href="#terms" className="text-zinc-500 hover:text-indigo-600 font-medium transition-colors">Terms of Service</Link></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-zinc-200 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-zinc-500 text-sm font-medium">
            © {new Date().getFullYear()} TalentLens Inc. All rights reserved.
          </p>
          <div className="flex gap-4 text-zinc-400">
            <Link href="#twitter" aria-label="Twitter" className="hover:text-indigo-600 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"/></svg>
            </Link>
            <Link href="#linkedin" aria-label="LinkedIn" className="hover:text-indigo-600 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/></svg>
            </Link>
            <Link href="#github" aria-label="GitHub" className="hover:text-indigo-600 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/></svg>
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <main className="min-h-screen bg-white selection:bg-indigo-100 selection:text-indigo-900 font-sans">
      <Navbar />
      <Hero />
      <TrustStrip />
      <WhyTalentLens />
      <ProductShowcase />
      <StatsBand />
      <Testimonials />
      <FinalCTA />
      <Footer />
    </main>
  );
}
