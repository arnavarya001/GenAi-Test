import { useState } from "react";
import { Copy, Check, FileText, ChevronDown, SearchX } from "lucide-react";

export default function AnswerCard({ msg, onOpenPage }) {
  const [copied, setCopied] = useState(false), [open, setOpen] = useState(false);
  if (msg.error) return <div className="card err" role="alert">{msg.error}</div>;
  if (!msg.found) return <div className="card nf"><SearchX size={18}/><strong>Not found</strong></div>;
  const copy = () => { navigator.clipboard.writeText(msg.answer); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  return (
    <div className="card">
      <div className="card-head"><span className="label">Answer</span>
        <button className="icon-btn" onClick={copy} aria-label="Copy answer">{copied ? <Check size={16}/> : <Copy size={16}/>}</button></div>
      <p className="answer">{msg.answer}</p>
      <button className="link" onClick={() => setOpen(!open)} aria-expanded={open}>
        <FileText size={15}/> Sources ({msg.citations.length}) <ChevronDown size={15} className={open ? "flip" : ""}/></button>
      {open && msg.citations.map((c, i) => (
        <div className="src" key={i}>
          <div className="meta"><b>{c.source}</b><span>{c.chapter || "Chapter: Not identified"}</span>
            <span>Section: {c.section || "Not identified"}</span>
            <span>PDF page {c.page} · Printed page {c.printed_page ?? "Not identified"}</span></div>
          <blockquote>{c.excerpt}</blockquote>
          <button className="btn-sm" onClick={() => onOpenPage(c.page)}>View page {c.page} in PDF</button>
        </div>))}
    </div>);
}
