import { useEffect, useRef, useState } from "react";
import { Scale, Plus, Send, BookOpen, X, Menu, Loader2 } from "lucide-react";
import AnswerCard from "./components/AnswerCard.jsx";

const SUGGESTED = [
  "How long does a proprietor have copyright in a registered design, and can it be extended?",
  "Which classification system is used to register designs?",
  "What is the government fee to register a trademark?",
  "Who is the current Controller General of Patents?",
  "What is the fee to register a design?"];

export default function App() {
  const [msgs, setMsgs] = useState([]), [input, setInput] = useState(""), [busy, setBusy] = useState(false);
  const [doc, setDoc] = useState(null), [docErr, setDocErr] = useState(""), [viewer, setViewer] = useState(null), [nav, setNav] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { fetch("/api/document").then(async r => r.ok ? setDoc(await r.json()) : setDocErr((await r.json()).detail))
    .catch(() => setDocErr("Backend is not reachable. Start it with: uvicorn main:app --reload")); }, []);
  useEffect(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), [msgs, busy]);

  async function send(text) {
    const q = (text ?? input).trim(); if (!q || busy) return;
    setInput(""); setBusy(true); setMsgs(m => [...m, { role: "user", text: q }]);
    try {
      const r = await fetch("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
      const d = await r.json();
      setMsgs(m => [...m, { role: "bot", ...(r.ok ? d : { error: d.detail || "Request failed" }) }]);
    } catch { setMsgs(m => [...m, { role: "bot", error: "Cannot reach the backend." }]); }
    setBusy(false);
  }
  const onKey = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };

  return (
    <div className="app">
      <aside className={"sidebar" + (nav ? " open" : "")}>
        <div className="brand"><Scale size={22}/> Designs Law Assistant</div>
        <button className="new" onClick={() => { setMsgs([]); setNav(false); }}><Plus size={16}/> New chat</button>
        <div className="side-sec">Document Library</div>
        <button className="doc-item" onClick={() => setViewer(1)}><BookOpen size={16}/>
          <span>{doc ? doc.title : "No document"}</span></button>
        {doc && <small className="stat">{doc.filename}<br/>{doc.pages} pages · {doc.indexed_chunks} chunks indexed</small>}
        {docErr && <small className="stat bad">{docErr}</small>}
        {doc && !doc.ready && <small className="stat bad">Not indexed yet. Run <code>python ingest.py</code> in backend/.</small>}
      </aside>
      <main className="main">
        <header className="top"><button className="icon-btn menu" onClick={() => setNav(!nav)} aria-label="Menu"><Menu size={20}/></button>
          <h2>Chat</h2>{doc && <span className={"pill " + (doc.ready ? "ok" : "bad")}>{doc.ready ? "Knowledge base ready" : "Not indexed"}</span>}</header>
        <div className="chat">
          {msgs.length === 0 && (<div className="welcome">
            <h1>Your Legal Document Assistant</h1>
            <p className="sub">Ask questions about industrial design registration in India.</p>
            <p className="desc">Answers come only from the <i>Manual of Designs Practice &amp; Procedure</i> (Office of the CGPDTM). The manual may not reflect later legal or fee changes.</p>
            <div className="cards">{SUGGESTED.map(q => <button key={q} className="sug" onClick={() => send(q)}>{q}</button>)}</div></div>)}
          {msgs.map((m, i) => m.role === "user" ? <div key={i} className="bubble user">{m.text}</div>
            : <AnswerCard key={i} msg={m} onOpenPage={setViewer}/>)}
          {busy && <div className="card loading"><Loader2 size={16} className="spin"/> Searching the manual…</div>}
          <div ref={endRef}/>
        </div>
        <div className="composer">
          <textarea rows={1} value={input} onChange={e => setInput(e.target.value)} onKeyDown={onKey}
            placeholder="Ask about design registration… (Enter to send, Shift+Enter for new line)" aria-label="Your question"/>
          <button className="send" onClick={() => send()} disabled={busy || !input.trim()} aria-label="Send"><Send size={18}/></button>
        </div>
      </main>
      {viewer && <section className="viewer"><div className="viewer-head"><b>PDF · page {viewer}</b>
        <button className="icon-btn" onClick={() => setViewer(null)} aria-label="Close"><X size={18}/></button></div>
        <iframe key={viewer} title="PDF" src={`/api/pdf#page=${viewer}`}/></section>}
    </div>);
}
