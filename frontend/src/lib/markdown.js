import MarkdownIt from 'markdown-it'

// html: false (default) -> raw HTML inside the model output is escaped, which
// keeps dangerouslySetInnerHTML safe from injection. breaks: single newlines
// become <br>. linkify: bare URLs become links.
const md = new MarkdownIt({ html: false, breaks: true, linkify: true })

export function renderMarkdown(text) {
  return md.render(text || '')
}
