import Link from "next/link";
import { Brain, Zap, GitBranch, BarChart3, Shield, ArrowRight, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";

const features = [
  {
    icon: Brain,
    title: "ML Models",
    description: "Train, deploy, and manage machine learning models with ease",
  },
  {
    icon: Zap,
    title: "Real-time Predictions",
    description: "Get instant predictions with low-latency inference engine",
  },
  {
    icon: GitBranch,
    title: "Data Pipelines",
    description: "Build and orchestrate automated data processing pipelines",
  },
  {
    icon: BarChart3,
    title: "Analytics Dashboard",
    description: "Comprehensive analytics and reporting for all your data",
  },
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "Bank-grade security with role-based access control",
  },
];

const benefits = [
  "Reduce manual decision-making by 80%",
  "Process millions of predictions per day",
  "Integrate with existing systems via REST API",
  "Real-time monitoring and alerting",
  "Explainable AI for transparent decisions",
];

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-pulse" style={{ animationDelay: "2s" }} />
      </div>

      {/* Navigation */}
      <nav className="relative z-10 flex items-center justify-between p-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-purple-500 to-blue-600 text-white p-2 rounded-xl">
            <Brain className="h-6 w-6" />
          </div>
          <span className="text-xl font-bold text-white">IEAP</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login">
            <Button variant="ghost" className="text-white hover:text-white hover:bg-white/10">
              Sign In
            </Button>
          </Link>
          <Link href="/register">
            <Button className="bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700">
              Get Started
            </Button>
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20 text-center">
        <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-full px-4 py-2 mb-8">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          <span className="text-sm text-white/80">Platform Status: All Systems Operational</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 leading-tight">
          Intelligent Enterprise
          <br />
          <span className="bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent">
            Automation Platform
          </span>
        </h1>

        <p className="text-xl text-white/70 max-w-2xl mx-auto mb-10">
          Harness the power of machine learning to automate decisions, streamline workflows, 
          and unlock insights from your enterprise data.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link href="/register">
            <Button size="lg" className="bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 text-lg px-8 py-6">
              Start Free Trial
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
          <Link href="/dashboard">
            <Button size="lg" variant="outline" className="text-lg px-8 py-6 border-white/20 text-white hover:bg-white/10">
              View Dashboard
            </Button>
          </Link>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Everything you need for enterprise AI
          </h2>
          <p className="text-lg text-white/60 max-w-2xl mx-auto">
            A complete platform for building, deploying, and managing AI-powered automation at scale.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 hover:bg-white/10 transition-colors"
            >
              <div className="bg-gradient-to-br from-purple-500 to-blue-600 w-12 h-12 rounded-xl flex items-center justify-center mb-4">
                <feature.icon className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-white/60">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Benefits Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 md:p-12">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
                Transform your business with AI
              </h2>
              <p className="text-lg text-white/60 mb-8">
                Join thousands of enterprises already using IEAP to automate complex decisions and scale their operations.
              </p>
              <ul className="space-y-4">
                {benefits.map((benefit, index) => (
                  <li key={index} className="flex items-center gap-3 text-white">
                    <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0" />
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-purple-500/20 to-blue-600/20 rounded-2xl p-6 text-center">
                <div className="text-4xl font-bold text-white mb-2">99.9%</div>
                <div className="text-white/60 text-sm">Uptime SLA</div>
              </div>
              <div className="bg-gradient-to-br from-purple-500/20 to-blue-600/20 rounded-2xl p-6 text-center">
                <div className="text-4xl font-bold text-white mb-2">10M+</div>
                <div className="text-white/60 text-sm">Predictions/Day</div>
              </div>
              <div className="bg-gradient-to-br from-purple-500/20 to-blue-600/20 rounded-2xl p-6 text-center">
                <div className="text-4xl font-bold text-white mb-2">&lt;50ms</div>
                <div className="text-white/60 text-sm">Avg Latency</div>
              </div>
              <div className="bg-gradient-to-br from-purple-500/20 to-blue-600/20 rounded-2xl p-6 text-center">
                <div className="text-4xl font-bold text-white mb-2">500+</div>
                <div className="text-white/60 text-sm">Enterprise Clients</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Ready to get started?
        </h2>
        <p className="text-lg text-white/60 mb-8 max-w-xl mx-auto">
          Start your free trial today and see how IEAP can transform your enterprise automation.
        </p>
        <Link href="/register">
          <Button size="lg" className="bg-gradient-to-r from-purple-500 to-blue-600 hover:from-purple-600 hover:to-blue-700 text-lg px-8 py-6">
            Start Free Trial
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
        </Link>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/10 py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-white/60" />
            <span className="text-white/60 text-sm">© 2024 IEAP. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-white/60">
            <Link href="/terms" className="hover:text-white">Terms</Link>
            <Link href="/privacy" className="hover:text-white">Privacy</Link>
            <Link href="/docs" className="hover:text-white">Documentation</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
