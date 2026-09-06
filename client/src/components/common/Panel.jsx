export default function Panel({ title, action, children, className = '' }) {
  return (
    <section
      className={`bg-panel border border-panel-border rounded-lg shadow-panel ${className}`}
    >
      {title && (
        <header className="flex items-center justify-between px-4 py-2.5 border-b border-panel-border">
          <h2 className="panel-label">{title}</h2>
          {action}
        </header>
      )}
      <div className="p-4">{children}</div>
    </section>
  );
}
