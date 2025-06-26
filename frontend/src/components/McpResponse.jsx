function McpResponse({ content }) {
  // content is the full JSON object: { status, message, ... }
  const { status, message, connection_url, dockerfile, error_details, server_name } = content;

  if (status === 'success') {
    return (
      <div className="p-4 bg-green-100 text-green-800 rounded-lg">
        <h3 className="font-bold">✅ Success: {server_name} Deployed</h3>
        <p>{message}</p>
        <p className="mt-2">
          <span>Connect at: </span>
          <a href={connection_url} target="_blank" rel="noopener noreferrer" className="font-mono bg-green-200 p-1 rounded">
            {connection_url}
          </a>
        </p>
        {/* Optional: Add a collapsible section for logs/dockerfile */}
        <details className="mt-2">
          <summary className="cursor-pointer">View Dockerfile & Logs</summary>
          <pre className="mt-2 p-2 bg-gray-800 text-white rounded-md text-xs overflow-x-auto">
            <code>
              <strong>Generated Dockerfile:</strong>{'\n'}{dockerfile}
            </code>
          </pre>
        </details>
      </div>
    );
  }

  if (status === 'failed') {
    return (
      <div className="p-4 bg-red-100 text-red-800 rounded-lg">
        <h3 className="font-bold">❌ Failed: {server_name} Deployment</h3>
        <p>{message}</p>
        <details className="mt-2">
          <summary className="cursor-pointer">View Error Logs & Dockerfile</summary>
          <pre className="mt-2 p-2 bg-gray-800 text-white rounded-md text-xs overflow-x-auto">
            <code>
              <strong>Error:</strong>{'\n'}{error_details}{'\n\n'}<strong>Attempted Dockerfile:</strong>{'\n'}{dockerfile}
            </code>
          </pre>
        </details>
      </div>
    );
  }

  // Handle other statuses like initial error
  return <div className="p-4 bg-yellow-100 text-yellow-800 rounded-lg">{content.message || content.error}</div>
}

export default McpResponse; 