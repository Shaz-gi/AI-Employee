import React from 'react';
import { Link } from 'react-router-dom';
import { 
  Mail, 
  Calendar, 
  TrendingUp, 
  Shield, 
  Zap, 
  Users,
  ArrowRight,
  CheckCircle,
  Sparkles,
  Menu,
  X
} from 'lucide-react';

function Landing() {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  return (
    <div className="min-h-screen overflow-x-hidden">
      {/* Navigation */}
      <nav className="relative z-50 glass border-b border-dark-700/50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2 group">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">AI Employee Pro</span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-dark-300 hover:text-white transition-colors">Features</a>
              <a href="#pricing" className="text-dark-300 hover:text-white transition-colors">Pricing</a>
              <a href="#about" className="text-dark-300 hover:text-white transition-colors">About</a>
              <Link to="/login" className="text-dark-300 hover:text-white transition-colors">Sign In</Link>
              <Link to="/signup" className="btn-primary">
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg hover:bg-dark-800 transition-all"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden mt-4 pb-4 border-t border-dark-700/50 pt-4">
              <div className="flex flex-col space-y-4">
                <a href="#features" className="text-dark-300 hover:text-white transition-colors">Features</a>
                <a href="#pricing" className="text-dark-300 hover:text-white transition-colors">Pricing</a>
                <a href="#about" className="text-dark-300 hover:text-white transition-colors">About</a>
                <Link to="/login" className="text-dark-300 hover:text-white transition-colors">Sign In</Link>
                <Link to="/signup" className="btn-primary justify-center">
                  Get Started
                </Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-20 pb-32 overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-float"></div>
          <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>
        </div>

        <div className="container mx-auto px-6 relative z-10">
          <div className="text-center max-w-4xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center space-x-2 bg-primary-500/10 border border-primary-500/20 rounded-full px-4 py-2 mb-8">
              <Sparkles className="w-4 h-4 text-primary-400" />
              <span className="text-sm text-primary-300">AI-Powered Automation</span>
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              Your <span className="gradient-text">Autonomous AI Employee</span>
              <br />
              That Works 24/7
            </h1>

            {/* Subheadline */}
            <p className="text-xl text-dark-300 mb-8 max-w-2xl mx-auto">
              Automate emails, schedule LinkedIn posts, and manage your business 
              with an AI assistant that never sleeps. Free tier includes 100 emails/month.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row justify-center gap-4 mb-16">
              <Link to="/signup" className="btn-primary text-lg px-8 py-4 justify-center">
                Start Free Trial
                <ArrowRight className="w-5 h-5" />
              </Link>
              <a 
                href="#features" 
                className="px-8 py-4 rounded-lg border border-dark-300 hover:border-primary-500 transition-all text-center hover:bg-dark-800"
              >
                Learn More
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
              <div className="glass p-6 rounded-xl card-hover">
                <div className="text-4xl font-bold gradient-text mb-2">50K+</div>
                <div className="text-dark-400">Emails Processed</div>
              </div>
              <div className="glass p-6 rounded-xl card-hover">
                <div className="text-4xl font-bold gradient-text mb-2">10K+</div>
                <div className="text-dark-400">Posts Scheduled</div>
              </div>
              <div className="glass p-6 rounded-xl card-hover">
                <div className="text-4xl font-bold gradient-text mb-2">100%</div>
                <div className="text-dark-400">Free to Start</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 relative">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Powerful <span className="gradient-text">Features</span>
            </h2>
            <p className="text-xl text-dark-300 max-w-2xl mx-auto">
              Everything you need to automate your business communications
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard
              icon={<Mail className="w-8 h-8" />}
              title="Smart Email Management"
              description="AI reads, analyzes, and drafts responses to your emails. Approve with one click."
            />
            <FeatureCard
              icon={<Calendar className="w-8 h-8" />}
              title="LinkedIn Automation"
              description="Schedule and auto-post engaging content. Grow your audience while you sleep."
            />
            <FeatureCard
              icon={<TrendingUp className="w-8 h-8" />}
              title="Usage Analytics"
              description="Track emails sent, posts scheduled, and engagement metrics in real-time."
            />
            <FeatureCard
              icon={<Shield className="w-8 h-8" />}
              title="Enterprise Security"
              description="Bank-level encryption, isolated data vaults, and complete audit trails."
            />
            <FeatureCard
              icon={<Zap className="w-8 h-8" />}
              title="Lightning Fast"
              description="Built on modern infrastructure. Process thousands of emails in seconds."
            />
            <FeatureCard
              icon={<Users className="w-8 h-8" />}
              title="Team Collaboration"
              description="Add team members, assign tasks, and manage approvals together."
            />
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 relative">
        <div className="container mx-auto px-6">
          {/* Section Header */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Simple, Transparent <span className="gradient-text">Pricing</span>
            </h2>
            <p className="text-xl text-dark-300 max-w-2xl mx-auto">
              Start free, upgrade as you grow
            </p>
          </div>

          {/* Pricing Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            <PricingCard
              tier="Free"
              price="$0"
              period="forever"
              features={[
                "100 emails/month",
                "10 LinkedIn posts/month",
                "Basic AI models",
                "Email support"
              ]}
              cta="Start Free"
              highlighted={false}
            />
            <PricingCard
              tier="Pro"
              price="$29"
              period="per month"
              features={[
                "1,000 emails/month",
                "50 LinkedIn posts/month",
                "Premium AI (GPT-4, Claude)",
                "Priority support",
                "Analytics dashboard",
                "Custom workflows"
              ]}
              cta="Go Pro"
              highlighted={true}
            />
            <PricingCard
              tier="Business"
              price="$99"
              period="per month"
              features={[
                "5,000 emails/month",
                "200 LinkedIn posts/month",
                "Everything in Pro",
                "5 team members",
                "API access",
                "Custom integrations",
                "SLA guarantee"
              ]}
              cta="Contact Sales"
              highlighted={false}
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 relative">
        <div className="container mx-auto px-6">
          <div className="glass rounded-3xl p-12 text-center border border-dark-700">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Ready to <span className="gradient-text">Get Started</span>?
            </h2>
            <p className="text-xl text-dark-300 mb-8 max-w-2xl mx-auto">
              Join thousands of entrepreneurs and businesses automating their workflows with AI Employee Pro.
            </p>
            <Link to="/signup" className="btn-primary text-lg px-8 py-4 inline-flex justify-center">
              Create Free Account
              <ArrowRight className="w-5 h-5" />
            </Link>
            <p className="text-dark-400 mt-4 text-sm">
              No credit card required • Free forever tier available
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dark-700 py-12">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <Sparkles className="w-6 h-6 text-primary-400" />
              <span className="text-xl font-bold gradient-text">AI Employee Pro</span>
            </div>
            <div className="text-dark-400 text-sm">
              © 2026 AI Employee Pro. Built with ❤️ for entrepreneurs.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="glass p-8 rounded-xl card-hover border border-dark-700/50">
      <div className="text-primary-400 mb-4">{icon}</div>
      <h3 className="text-xl font-bold mb-3 text-white">{title}</h3>
      <p className="text-dark-300 leading-relaxed">{description}</p>
    </div>
  );
}

function PricingCard({ tier, price, period, features, cta, highlighted }) {
  return (
    <div className={`glass p-8 rounded-xl card-hover border ${
      highlighted ? 'border-primary-500 border-2' : 'border-dark-700'
    }`}>
      <div className="text-center mb-8">
        <div className="text-dark-400 text-sm mb-2">{tier}</div>
        <div className="text-5xl font-bold gradient-text mb-2">{price}</div>
        <div className="text-dark-400 text-sm">{period}</div>
      </div>
      <ul className="space-y-4 mb-8">
        {features.map((feature, index) => (
          <li key={index} className="flex items-start space-x-3">
            <CheckCircle className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5" />
            <span className="text-dark-300">{feature}</span>
          </li>
        ))}
      </ul>
      <button className={`w-full py-3 rounded-lg font-semibold transition-all ${
        highlighted 
          ? 'btn-primary' 
          : 'border border-dark-300 hover:border-primary-500 hover:bg-dark-800'
      }`}>
        {cta}
      </button>
    </div>
  );
}

export default Landing;
