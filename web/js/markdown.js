/**
 * Lightweight Markdown → HTML renderer.
 *
 * Supports: headings, bold, italic, inline code, code blocks,
 * unordered/ordered lists, blockquotes, links, horizontal rules.
 *
 * Security: All text is HTML-escaped FIRST, then Markdown syntax is
 * converted to safe HTML elements. Links are validated to prevent
 * javascript: URI injection.
 *
 * No external dependencies.
 */
const MarkdownRenderer = (() => {
    /**
     * Convert a Markdown string to safe HTML.
     * @param {string} md - Raw Markdown text.
     * @returns {string} HTML string.
     */
    function render(md) {
        if (!md) return "";

        let html = md;

        // Normalize line endings
        html = html.replace(/\r\n/g, "\n");

        // ── Step 1: Extract fenced code blocks and replace with placeholders ──
        const codeBlocks = [];
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_m, _lang, code) => {
            const idx = codeBlocks.length;
            codeBlocks.push(`<pre><code>${escapeHtml(code.trim())}</code></pre>`);
            return `\x00CODEBLOCK${idx}\x00`;
        });

        // ── Step 2: Extract inline code and replace with placeholders ──
        const inlineCodes = [];
        html = html.replace(/`([^`]+)`/g, (_m, code) => {
            const idx = inlineCodes.length;
            inlineCodes.push(`<code>${escapeHtml(code)}</code>`);
            return `\x00INLINECODE${idx}\x00`;
        });

        // ── Step 3: Escape ALL remaining HTML to prevent XSS ──
        html = escapeHtml(html);

        // ── Step 4: Apply Markdown transforms on escaped text ──

        // Blockquotes (&gt; text — the '>' is now escaped)
        html = html.replace(/^&gt;\s?(.*)$/gm, "<blockquote>$1</blockquote>");
        html = html.replace(/<\/blockquote>\n<blockquote>/g, "\n");

        // Headings (### escaped to ### since # is not an HTML entity)
        html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
        html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
        html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

        // Horizontal rule
        html = html.replace(/^---+$/gm, "<hr>");

        // Bold & italic (asterisks were escaped to &ast; ... no, * is not HTML-special)
        // Since escapeHtml only escapes &<>"', asterisks survive intact:
        html = html.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
        html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");

        // Links [text](url) — url was escaped so &quot; etc.
        // We need to unescape the URL and then validate it
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_m, text, rawUrl) => {
            const url = unescapeHtml(rawUrl);
            if (!isSafeUrl(url)) return text; // strip unsafe links, show text only
            return `<a href="${escapeAttr(url)}" target="_blank" rel="noopener noreferrer">${text}</a>`;
        });

        // Unordered lists (- item or * item)
        html = html.replace(/^(?:[-*])\s+(.+)$/gm, "<li>$1</li>");
        html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

        // Ordered lists (1. item)
        html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>");
        html = html.replace(/(?<!<\/ul>)\n(<li>)/g, "<ol>$1");
        html = html.replace(/(<\/li>)\n(?!<li>)/g, "$1</ol>");

        // Paragraphs: wrap remaining loose lines
        html = html
            .split("\n\n")
            .map((block) => {
                block = block.trim();
                if (!block) return "";
                if (/^<[a-z]/.test(block)) return block;
                return `<p>${block.replace(/\n/g, "<br>")}</p>`;
            })
            .join("\n");

        // ── Step 5: Restore code placeholders ──
        html = html.replace(/\x00CODEBLOCK(\d+)\x00/g, (_m, idx) => codeBlocks[parseInt(idx, 10)]);
        html = html.replace(/\x00INLINECODE(\d+)\x00/g, (_m, idx) => inlineCodes[parseInt(idx, 10)]);

        return html;
    }

    /** Escape HTML entities to prevent XSS. */
    function escapeHtml(str) {
        const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" };
        return str.replace(/[&<>"']/g, (c) => map[c]);
    }

    /** Unescape HTML entities (for URL processing). */
    function unescapeHtml(str) {
        const map = { "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#039;": "'" };
        return str.replace(/&amp;|&lt;|&gt;|&quot;|&#039;/g, (e) => map[e]);
    }

    /** Escape a string for safe use in an HTML attribute value. */
    function escapeAttr(str) {
        return str.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/'/g, "&#039;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    /** Only allow http(s) and mailto links — blocks javascript:, data:, vbscript:, etc. */
    function isSafeUrl(url) {
        const trimmed = url.trim().toLowerCase();
        if (trimmed.startsWith("http://") || trimmed.startsWith("https://") || trimmed.startsWith("mailto:")) {
            return true;
        }
        // Allow relative URLs (no colon before first slash)
        if (!trimmed.includes(":")) return true;
        return false;
    }

    return { render };
})();
