import Link from "next/link";
import { Button } from "@/components/ui/button";
import { ArrowRight, BarChart3, ShieldCheck, Database } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-zinc-50 dark:bg-black">
      <main className="flex-1 flex flex-col items-center justify-center text-center px-4">
        <div className="space-y-6 max-w-3xl">
          <h1 className="text-5xl font-extrabold tracking-tight sm:text-6xl text-zinc-900 dark:text-zinc-50">
            Meet Your <span className="text-primary">AI Data Analyst</span>
          </h1>
          <p className="text-xl text-zinc-600 dark:text-zinc-400 max-w-2xl mx-auto">
            Upload your CSV/Excel files and instantly get clean data, automated EDA, beautiful visualizations, and deep business insights powered by Groq & ChromaDB.
          </p>
          <div className="pt-8">
            <Link href="/login">
              <Button size="lg" className="h-12 px-8 text-lg font-medium rounded-full shadow-lg">
                Get Started <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-5xl mx-auto">
          <div className="flex flex-col items-center p-6 bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
            <div className="p-3 bg-primary/10 rounded-full mb-4">
              <Database className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-bold mb-2">Automated EDA</h3>
            <p className="text-zinc-600 dark:text-zinc-400">Instantly clean data and generate summary statistics without writing a single line of code.</p>
          </div>
          <div className="flex flex-col items-center p-6 bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
            <div className="p-3 bg-primary/10 rounded-full mb-4">
              <BarChart3 className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-bold mb-2">RAG Chat</h3>
            <p className="text-zinc-600 dark:text-zinc-400">Talk to your data naturally. The system retrieves past insights and answers questions via vector search.</p>
          </div>
          <div className="flex flex-col items-center p-6 bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800">
            <div className="p-3 bg-primary/10 rounded-full mb-4">
              <ShieldCheck className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-bold mb-2">Secure & Audited</h3>
            <p className="text-zinc-600 dark:text-zinc-400">Built-in prompt injection defense, JWT authentication, and full audit logging for enterprise security.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
