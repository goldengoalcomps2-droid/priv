import { Search, Plus } from "lucide-react";

export function TopBar() {
  return (
    <header className="bg-page border-b border-rule px-8 py-4 flex items-center gap-4">
      <div className="flex-1" />
      <label className="relative">
        <span className="sr-only">Search vehicles, customers</span>
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-subtle" aria-hidden />
        <input
          type="search"
          placeholder="Search vehicles, customers..."
          className="w-80 rounded-lg border border-rule bg-card pl-9 pr-3 py-2 text-sm placeholder:text-ink-subtle"
        />
      </label>
      <button
        type="button"
        className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-hover focus-visible:outline-2"
      >
        <Plus className="h-4 w-4" aria-hidden /> New Rental
      </button>
    </header>
  );
}
