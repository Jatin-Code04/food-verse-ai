import React, { useEffect, useMemo, useState } from 'react';
import { Activity, Apple, ArrowRight, Camera, ChefHat, CheckCircle2, CircleHelp, Clock3, FileText, Flame, HeartPulse, ImagePlus, Leaf, LoaderCircle, Menu, Salad, ShieldCheck, Sparkles, Utensils, Video, X } from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8001';
const modules = [
  { id: 'overview', label: 'Overview', icon: Activity, eyebrow: 'YOUR FOOD, UNDERSTOOD', title: 'A smarter way to look at food.', desc: 'Explore nutrition, freshness, kitchen hygiene and meal ideas in one place.', color: 'mint' },
  { id: 'food', label: 'Food Recognition', icon: Apple, eyebrow: 'MULTIMODAL FOOD LENS', title: 'Know what is on your plate.', desc: 'Upload a food photo to explore dish identification and estimated nutrition.', color: 'green' },
  { id: 'freshness', label: 'Freshness Detector', icon: Sparkles, eyebrow: 'VISUAL FRESHNESS CHECK', title: 'Look for visible signs of freshness.', desc: 'Review visible condition alongside storage and handling context.', color: 'orange' },
  { id: 'hygiene', label: 'Hygiene Monitor', icon: ShieldCheck, eyebrow: 'KITCHEN SAFETY REVIEW', title: 'Make the next check count.', desc: 'Review a kitchen photo and build a simple checklist for follow-up.', color: 'blue' },
  { id: 'recipe', label: 'Smart Kitchen', icon: ChefHat, eyebrow: 'SMART RECIPE GENERATOR', title: 'Turn ingredients into dinner.', desc: 'Share what you have and get a practical recipe idea.', color: 'coral' },
  { id: 'planner', label: 'Meal Planner', icon: Salad, eyebrow: 'PERSONALIZED MEAL PLANNER', title: 'Make room for better habits.', desc: 'Get flexible meal ideas based on your preferences and goals.', color: 'purple' },
];

async function sendForm(path, form) {
  const response = await fetch(`${API_BASE}${path}`, { method: 'POST', body: form });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}
async function sendJson(path, body) {
  const response = await fetch(`${API_BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function ResultPanel({ data }) {
  if (!data) return null;
  const entries = Object.entries(data).filter(([key]) => !['mode'].includes(key));
  const pretty = value => Array.isArray(value) ? <ul>{value.map((v, i) => <li key={i}>{typeof v === 'object' ? `${v.meal || ''}: ${(v.suggestions || []).join(', ')}` : String(v)}</li>)}</ul> : value && typeof value === 'object' ? <ul>{Object.entries(value).map(([k,v]) => <li key={k}><b>{k.replaceAll('_',' ')}:</b> {String(v)}</li>)}</ul> : String(value ?? 'Not available');
  return <section className="result-panel"><div className="result-head"><div><span className="eyebrow">ANALYSIS RESULT</span><h3>{data.dish_name || data.title || data.item || data.overall_status || 'Your result'}</h3></div><span className={`mode-pill ${data.mode === 'live AI' ? 'live' : ''}`}>{data.mode || 'result'}</span></div><div className="result-grid">{entries.map(([key, value]) => <div className="result-item" key={key}><span>{key.replaceAll('_',' ')}</span><div>{pretty(value)}</div></div>)}</div><p className="disclaimer"><CircleHelp size={15}/> Estimates and visual observations can be wrong. Verify food safety independently.</p></section>;
}

function ImageField({ file, setFile, preview, setPreview, label = 'Upload an image' }) {
  return <label className="upload-box"><input type="file" accept="image/*" onChange={e => { const f=e.target.files?.[0]; if (f) { setFile(f); setPreview(URL.createObjectURL(f)); } }} /><span className="upload-icon"><ImagePlus size={22}/></span><strong>{file ? file.name : label}</strong><small>JPG, PNG or WEBP · up to 8 MB</small>{preview && <img className="image-preview" src={preview} alt="Selected upload preview"/>}</label>;
}

function ModuleContent({ active }) {
  const [file, setFile] = useState(null); const [preview, setPreview] = useState('');
  const [context, setContext] = useState(''); const [storage, setStorage] = useState('Refrigerated'); const [age, setAge] = useState('1 day');
  const [ingredients, setIngredients] = useState('Potato, onion, tomato, peas'); const [cuisine, setCuisine] = useState('Indian'); const [servings, setServings] = useState('2'); const [dietary, setDietary] = useState('Vegetarian');
  const [goal, setGoal] = useState('Balanced eating'); const [diet, setDiet] = useState('Vegetarian'); const [allergies, setAllergies] = useState('None'); const [notes, setNotes] = useState(''); const [observations, setObservations] = useState('Clean surfaces, food storage and handwashing station');
  const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [result, setResult] = useState(null);
  useEffect(() => { setFile(null); setPreview(''); setResult(null); setError(''); }, [active]);
  const run = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      let data;
     if (active === 'recipe') {
  const form = new FormData();
  form.append('ingredients', ingredients);
  form.append('cuisine', cuisine);
  form.append('servings', servings);
  form.append('dietary_preferences', dietary);
  if (file) form.append('file', file);
  data = await sendForm('/api/recipe', form);
}
      else if (active === 'planner') data = await sendJson('/api/meal-plan', { age: 20, goal, diet, allergies, meals_per_day: 4, notes });
      else {
        const form = new FormData(); if (file) form.append('file', file);
        if (active === 'food') { form.append('context', context); data = await sendForm('/api/analyze-food', form); }
        if (active === 'freshness') { form.append('storage', storage); form.append('age', age); data = await sendForm('/api/freshness', form); }
        if (active === 'hygiene') { form.append('observations', observations); data = await sendForm('/api/hygiene', form); }
      }
      setResult(data)
    } catch (e) { setError(`${e.message}. Make sure the backend is running on port 8000.`); }
    finally { setLoading(false); }
  };
  if (active === 'overview') return <div className="overview-content"><div className="welcome-card"><div><span className="eyebrow">GOOD FOOD STARTS WITH GOOD INFORMATION</span><h2>Welcome to <em>FoodVerse AI</em></h2><p>A practical workspace for understanding the food you eat, cook and serve.</p><button className="primary-btn" onClick={() => window.dispatchEvent(new CustomEvent('foodverse:navigate', {detail:'food'}))}>Start an analysis <ArrowRight size={16}/></button></div><div className="hero-orbit"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="hero-apple"><Apple size={72}/><Sparkles size={24}/></div></div></div><div className="section-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h3>Explore the modules</h3></div><span className="muted">5 tools · one dashboard</span></div><div className="module-cards">{modules.slice(1).map(m => <button className="module-card" key={m.id} onClick={() => window.dispatchEvent(new CustomEvent('foodverse:navigate', {detail:m.id}))}><span className={`module-icon ${m.color}`}><m.icon size={21}/></span><span className="card-title">{m.label}</span><span className="card-desc">{m.desc}</span><span className="card-link">Open module <ArrowRight size={14}/></span></button>)}</div><div className="bottom-note"><ShieldCheck size={18}/><span><b>Thoughtful by design</b><br/>AI results are estimates. Use your judgement and trusted food-safety guidance.</span></div></div>;
  return <div className="tool-content"><div className={`tool-banner ${active}`}><span className="module-icon"><ActiveIcon active={active}/></span><div><span className="eyebrow">{modules.find(m=>m.id===active)?.eyebrow}</span><h2>{modules.find(m=>m.id===active)?.title}</h2><p>{modules.find(m=>m.id===active)?.desc}</p></div></div>
    <div className="form-card">
      {['food','freshness','hygiene'].includes(active) && <ImageField file={file} setFile={setFile} preview={preview} setPreview={setPreview} label={active === 'food' ? 'Choose a food photo' : active === 'freshness' ? 'Upload produce or food photo' : 'Upload a kitchen photo'}/>}
      {active === 'food' && <label className="field"><span>Extra context <small>(optional)</small></span><textarea value={context} onChange={e=>setContext(e.target.value)} placeholder="e.g. homemade paneer wrap, medium portion" rows="3"/></label>}
      {active === 'freshness' && <div className="two-fields"><label className="field"><span>Storage condition</span><select value={storage} onChange={e=>setStorage(e.target.value)}><option>Refrigerated</option><option>Room temperature</option><option>Frozen</option><option>Unknown</option></select></label><label className="field"><span>Time since purchase / prep</span><select value={age} onChange={e=>setAge(e.target.value)}><option>Unknown</option><option>Same day</option><option>1 day</option><option>2–3 days</option><option>More than 3 days</option></select></label></div>}
      {active === 'hygiene' && <label className="field"><span>Inspection notes</span><textarea rows="3" value={observations} onChange={e=>setObservations(e.target.value)}/></label>}
     {active === 'recipe' && <>
  <label className="field">
    <span>Ingredients you have</span>
    <textarea
      rows="4"
      value={ingredients}
      onChange={e => setIngredients(e.target.value)}
      placeholder="e.g. potato, onion, tomato, peas"
    />
  </label>
  <label className="field">
    <span>Or upload an ingredient photo (optional)</span>
    <input
      type="file"
      accept="image/*"
      onChange={e => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
          setFile(selectedFile);
          setPreview(URL.createObjectURL(selectedFile));
        }
      }}
    />
  </label>
</>}
      {active === 'planner' && <><div className="two-fields"><label className="field"><span>Main goal</span><select value={goal} onChange={e=>setGoal(e.target.value)}>{['Balanced eating','Build healthy habits','More plant-based meals','High-protein ideas','Budget-friendly meals'].map(x=><option key={x}>{x}</option>)}</select></label><label className="field"><span>Diet type</span><select value={diet} onChange={e=>setDiet(e.target.value)}>{['Vegetarian','Vegan','Non-vegetarian','No preference'].map(x=><option key={x}>{x}</option>)}</select></label></div><label className="field"><span>Allergies or restrictions</span><input value={allergies} onChange={e=>setAllergies(e.target.value)} placeholder="e.g. peanuts, lactose, none"/></label><label className="field"><span>Anything else? <small>(optional)</small></span><textarea rows="3" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Budget, foods you like, schedule..."/></label></>}
      <button className="primary-btn run-btn" onClick={run} disabled={loading}>{loading ? <><LoaderCircle className="spin" size={17}/> Working…</> : <>{active==='recipe' ? 'Generate recipe' : active==='planner' ? 'Build my meal ideas' : active==='hygiene' ? 'Review hygiene' : active==='freshness' ? 'Check visible condition' : 'Analyze food'} <ArrowRight size={16}/></>}</button>
      {error && <div className="error-box"><X size={16}/>{error}</div>}
    </div>
    {result && <ResultPanel data={result}/>}
    <p className="module-footnote"><ShieldCheck size={15}/> {active==='hygiene' ? 'Prototype only; not a certified compliance inspection.' : active==='freshness' ? 'Photos cannot prove food is safe. When in doubt, discard it.' : active==='planner' ? 'General meal ideas only, not medical or dietetic advice.' : active==='food' ? 'Nutrition estimates depend on ingredients and portion sizes.' : 'Check allergies and cook food thoroughly.'}</p>
  </div>;
}
function ActiveIcon({active}) { const I = modules.find(m=>m.id===active)?.icon || Apple; return <I size={21}/>; }

export default function App() {
  const [active, setActive] = useState('overview'); const [apiStatus, setApiStatus] = useState('checking'); const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => { fetch(`${API_BASE}/api/health`).then(r=>r.json()).then(d=>setApiStatus(d.ai_mode === 'live' ? 'live' : 'demo')).catch(()=>setApiStatus('offline')); }, []);
  useEffect(() => { const handler=e=>{setActive(e.detail); setMobileOpen(false);}; window.addEventListener('foodverse:navigate',handler); return ()=>window.removeEventListener('foodverse:navigate',handler); }, []);
  const current = modules.find(m=>m.id===active) || modules[0];
  return <div className="app-shell"><aside className={`sidebar ${mobileOpen?'open':''}`}><div className="brand"><span className="brand-mark"><Utensils size={20}/></span><span>Food<span>Verse</span><small>AI INTELLIGENCE</small></span><button className="mobile-close" onClick={()=>setMobileOpen(false)}><X size={18}/></button></div><div className="nav-label">WORKSPACE</div><nav>{modules.map(m=><button key={m.id} className={`nav-item ${active===m.id?'active':''}`} onClick={()=>{setActive(m.id);setMobileOpen(false)}}><m.icon size={17}/><span>{m.label}</span>{active===m.id&&<span className="nav-dot"/>}</button>)}</nav><div className="sidebar-bottom"><div className="status-card"><div className="status-top"><span className={`status-dot ${apiStatus}`}/><span>System status</span><span className="status-value">{apiStatus==='offline'?'Offline':apiStatus==='checking'?'Checking':apiStatus==='live'?'AI live':'Demo'}</span></div><div className="status-bar"><span style={{width:apiStatus==='offline'?'18%':apiStatus==='live'?'100%':'65%'}}/></div><small>{apiStatus==='offline'?'Start the backend server':'FoodVerse services'}</small></div><div className="profile"><div className="avatar">JC</div><div><b>Jatin Chouhan</b><small>Project workspace</small></div><span className="profile-menu">•••</span></div></div></aside>
    {mobileOpen&&<button className="scrim" onClick={()=>setMobileOpen(false)} aria-label="Close navigation"/>}<main className="main-area"><header className="topbar"><button className="menu-toggle" onClick={()=>setMobileOpen(true)}><Menu size={20}/></button><div className="breadcrumbs"><span>Workspace</span><span className="crumb-slash">/</span><b>{current.label}</b></div><div className="topbar-right"><span className="top-pill"><span className={`status-dot ${apiStatus}`}/>{apiStatus==='live'?'AI Connected':apiStatus==='offline'?'Backend Offline':apiStatus==='checking'?'Connecting':'Demo Mode'}</span><div className="top-avatar">JC</div></div></header><div className="page-wrap"><div className="page-heading"><div><span className="eyebrow">FOOD INTELLIGENCE PLATFORM</span><h1>{active==='overview'?'Your food, in better focus.':current.label}</h1></div><div className="date-chip"><Sparkles size={15}/> Multimodal AI</div></div><ModuleContent key={active} active={active}/><footer className="footer"><span>FoodVerse AI <span className="muted">· Student project prototype</span></span><span>Built for informed food choices</span></footer></div></main></div>;
}
