import React, { useState } from 'react';
import { MessageSquare, Send, X } from 'lucide-react';

export const ChatWidget = () => {
  const [showChat, setShowChat] = useState(false);
  const [chatInput, setChatInput] = useState('');
  const [chatHistory, setChatHistory] = useState([
    { role: 'ai', content: 'こんにちは！AIコンシェルジュです。今日のレースについて何かお手伝いしましょうか？' }
  ]);

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: 'user', content: chatInput };
    setChatHistory([...chatHistory, userMsg]);
    setChatInput('');

    try {
      const resp = await fetch('http://localhost:8001/api/concierge/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: chatInput })
      });
      const data = await resp.json();
      setChatHistory(prev => [...prev, { role: 'ai', content: data.answer }]);
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'ai', content: 'エラーが発生しました。' }]);
    }
  };

  return (
    <>
      <button
        onClick={() => setShowChat(!showChat)}
        style={{
          position: 'fixed', bottom: '2rem', right: '2rem',
          width: '60px', height: '60px', borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--primary), var(--success))',
          border: 'none', cursor: 'pointer', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 20px rgba(0,242,255,0.4)'
        }}
      >
        <MessageSquare size={28} color="#000" />
      </button>

      {showChat && (
        <div style={{
          position: 'fixed', bottom: '6rem', right: '2rem',
          width: '350px', height: '450px',
          background: 'var(--card-bg)', borderRadius: '16px',
          border: '1px solid var(--glass-border)',
          display: 'flex', flexDirection: 'column',
          zIndex: 1000, overflow: 'hidden'
        }}>
          <div style={{
            padding: '1rem', borderBottom: '1px solid var(--glass-border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ fontWeight: '700' }}>🤖 AIコンシェルジュ</span>
            <button onClick={() => setShowChat(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
            {chatHistory.map((msg, i) => (
              <div key={i} style={{
                marginBottom: '0.75rem',
                textAlign: msg.role === 'user' ? 'right' : 'left'
              }}>
                <span style={{
                  display: 'inline-block',
                  padding: '0.5rem 1rem', borderRadius: '12px',
                  background: msg.role === 'user' ? 'var(--primary)' : 'rgba(255,255,255,0.1)',
                  color: msg.role === 'user' ? '#000' : '#fff',
                  maxWidth: '80%'
                }}>
                  {msg.content}
                </span>
              </div>
            ))}
          </div>
          <div style={{ padding: '1rem', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: '0.5rem' }}>
            <input
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && sendChatMessage()}
              placeholder="質問を入力..."
              style={{
                flex: 1, padding: '0.75rem',
                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)',
                borderRadius: '8px', color: '#fff'
              }}
            />
            <button onClick={sendChatMessage} className="btn-primary" style={{ padding: '0.75rem' }}>
              <Send size={18} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};

export default ChatWidget;
