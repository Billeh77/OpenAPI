function McpResponse({ content }) {
  // content is the full JSON object: { status, message, ... }
  const { status, message, connection_url, deployment_files, dockerfile, error_details, server_name } = content;

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
        {/* Optional: Add a collapsible section for deployment files */}
        <details className="mt-2">
          <summary className="cursor-pointer">
            View Deployment Files ({deployment_files ? Object.keys(deployment_files).length : '1'} files)
          </summary>
          <div className="mt-2 space-y-3">
            {deployment_files ? (
              Object.entries(deployment_files).map(([filename, content]) => (
                <div key={filename} className="border rounded">
                  <div className="bg-gray-200 px-3 py-2 font-medium text-sm border-b">
                    📄 {filename}
                  </div>
                  <pre className="p-3 bg-gray-800 text-white text-xs overflow-x-auto max-h-64">
                    <code>{content}</code>
                  </pre>
                </div>
              ))
            ) : dockerfile ? (
              <div className="border rounded">
                <div className="bg-gray-200 px-3 py-2 font-medium text-sm border-b">
                  📄 Dockerfile
                </div>
                <pre className="p-3 bg-gray-800 text-white text-xs overflow-x-auto max-h-64">
                  <code>{dockerfile}</code>
                </pre>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">No deployment files available</p>
            )}
          </div>
        </details>
      </div>
    );
  }

  if (status === 'failed') {
    const { error_history, total_attempts } = content;
    return (
      <div className="p-4 bg-red-100 text-red-800 rounded-lg">
        <h3 className="font-bold">❌ Failed: {server_name} Deployment</h3>
        <p>{message}</p>
        {total_attempts && (
          <p className="text-sm mt-1">Total attempts: {total_attempts}</p>
        )}
        <details className="mt-2">
          <summary className="cursor-pointer">View Error Logs & Final Deployment Files</summary>
          <div className="mt-2 space-y-3">
            <div className="p-3 bg-gray-800 text-white text-xs rounded overflow-x-auto max-h-32">
              <strong>Latest Error:</strong><br />
              {error_details}
            </div>
            {deployment_files ? (
              <div className="space-y-2">
                <strong className="text-sm">Final Deployment Files:</strong>
                {Object.entries(deployment_files).map(([filename, content]) => (
                  <div key={filename} className="border rounded">
                    <div className="bg-gray-200 px-3 py-2 font-medium text-sm border-b">
                      📄 {filename}
                    </div>
                    <pre className="p-3 bg-gray-800 text-white text-xs overflow-x-auto max-h-32">
                      <code>{content.substring(0, 500)}{content.length > 500 ? '...' : ''}</code>
                    </pre>
                  </div>
                ))}
              </div>
            ) : dockerfile ? (
              <div className="border rounded">
                <div className="bg-gray-200 px-3 py-2 font-medium text-sm border-b">
                  📄 Final Dockerfile
                </div>
                <pre className="p-3 bg-gray-800 text-white text-xs overflow-x-auto max-h-32">
                  <code>{dockerfile}</code>
                </pre>
              </div>
            ) : null}
          </div>
        </details>
        {error_history && error_history.length > 1 && (
          <details className="mt-2">
            <summary className="cursor-pointer">View All Attempts ({error_history.length})</summary>
            <div className="mt-2 space-y-2">
              {error_history.map((attempt, index) => (
                <div key={index} className="p-2 bg-gray-100 rounded text-xs">
                  <strong>Attempt {attempt.attempt} ({attempt.status}):</strong>
                  <pre className="mt-1 p-1 bg-gray-800 text-white rounded text-xs overflow-x-auto max-h-32">
                    {attempt.error.substring(0, 300)}...
                  </pre>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    );
  }

  // Handle other statuses like initial error
  return <div className="p-4 bg-yellow-100 text-yellow-800 rounded-lg">{content.message || content.error}</div>
}

export default McpResponse; 