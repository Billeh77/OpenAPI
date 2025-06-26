import { useState, useRef, useEffect } from "react";
import axios from "axios";
import McpResponse from "./McpResponse";

export default function Chat() {
  const [input, setInput] = useState("");
  const [log, setLog] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const endOfMessagesRef = useRef(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [log]);

  const send = async () => {
    if (!input || isLoading) return;

    const userMessage = { q: input, a: null, type: 'text' };
    setLog(prevLog => [...prevLog, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const { data } = await axios.post("http://localhost:8000/chat", { message: input });
      
      // Create a new assistant message object
      const assistantMessage = {
        q: input,
        // Use a special type to render this message differently
        type: 'mcp_response', 
        a: data // The entire JSON object from the backend
      };
      
      setLog(prevLog => {
        const newLog = [...prevLog];
        newLog[newLog.length - 1] = assistantMessage;
        return newLog;
      });

    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message || "An unexpected error occurred.";
      setLog(prevLog => {
        const newLog = [...prevLog];
        newLog[newLog.length - 1].a = `Error: ${errorMessage}`;
        newLog[newLog.length - 1].type = 'text';
        return newLog;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      send();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 p-4 max-w-2xl mx-auto">
      <header className="mb-4 text-center">
        <h1 className="text-3xl font-bold text-gray-800">Universal MCP Adapter</h1>
        <p className="text-sm text-gray-500">Request MCP servers and get them deployed automatically!</p>
      </header>
      <div className="flex-1 border rounded-lg bg-white shadow-inner p-4 overflow-y-auto mb-4">
        {log.map((l, i) => (
          <div key={i} className="mb-4 last:mb-0">
            <div className="font-semibold text-gray-700">You: {l.q}</div>
            <div className="mt-1">
              <span className="font-semibold text-blue-600">MCP Adapter: </span>
              {l.a === null ? (
                <div className="animate-pulse flex space-x-2 mt-2">
                    <div className="h-2 w-2 bg-slate-300 rounded-full"></div>
                    <div className="h-2 w-2 bg-slate-300 rounded-full"></div>
                    <div className="h-2 w-2 bg-slate-300 rounded-full"></div>
                </div>
              ) : l.type === 'mcp_response' ? (
                <div className="mt-2">
                  <McpResponse content={l.a} />
                </div>
              ) : (
                <pre className="bg-gray-100 p-3 rounded-md text-sm text-gray-800 whitespace-pre-wrap break-words">{l.a}</pre>
              )}
            </div>
          </div>
        ))}
        <div ref={endOfMessagesRef} />
      </div>
      <div className="flex">
        <input 
          className="flex-1 border rounded-l-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500" 
          value={input} 
          onChange={e => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="I need a tool to manage files..."
          disabled={isLoading}
        />
        <button 
          className="px-6 py-2 bg-blue-600 text-white rounded-r-lg hover:bg-blue-700 disabled:bg-blue-300 transition-colors" 
          onClick={send}
          disabled={isLoading}
        >
          Send
        </button>
      </div>
    </div>
  );
} 