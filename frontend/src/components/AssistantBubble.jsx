export default function AssistantBubble({ content }) {
  const rendered = content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\n/g, '<br/>')

  const withLinks = rendered.replace(
    /(https?:\/\/[^\s<]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
  )

  return (
    <div
      className="assistant-bubble"
      dangerouslySetInnerHTML={{ __html: withLinks }}
    />
  )
}
