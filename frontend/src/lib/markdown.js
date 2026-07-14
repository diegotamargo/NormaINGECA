import MarkdownIt from 'markdown-it'
import texmath from 'markdown-it-texmath'
import katex from 'katex'

// html: false (default) -> raw HTML inside the model output is escaped, which
// keeps dangerouslySetInnerHTML safe from injection. breaks: single newlines
// become <br>. linkify: bare URLs become links.
const md = new MarkdownIt({ html: false, breaks: true, linkify: true })

// LaTeX math support. The model answers technical questions with formulas in
// $...$ (inline) and $$...$$ (display) — texmath + KaTeX turn those into
// rendered equations instead of raw "$\sqrt{...}$" text.
//   - delimiters: 'dollars' handles both $inline$ and $$display$$.
//   - throwOnError: false -> a malformed or still-streaming (unclosed) formula
//     renders as a small error node instead of throwing and breaking the whole
//     message while tokens are still arriving.
md.use(texmath, {
  engine: katex,
  delimiters: 'dollars',
  katexOptions: { throwOnError: false },
})

export function renderMarkdown(text) {
  return md.render(text || '')
}
