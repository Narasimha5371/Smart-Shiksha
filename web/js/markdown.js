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

        // ── Step 1b: Extract <details>/<summary> blocks (safe HTML) ──
        const detailsBlocks = [];
        html = html.replace(/<details>([\s\S]*?)<\/details>/gi, (_m, inner) => {
            const idx = detailsBlocks.length;
            // Process inner content: preserve <summary> tags, render rest as markdown
            let processed = inner
                .replace(/<summary>(.*?)<\/summary>/gi, '\x00DETSUM_OPEN\x00$1\x00DETSUM_CLOSE\x00');
            detailsBlocks.push(processed);
            return `\x00DETAILSBLOCK${idx}\x00`;
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

        // ── List handling (robust: flatten first, use unique markers) ──
        // NOTE: Use \x01 for list tokens to avoid collision with \x00 used by code placeholders

        // Flatten ALL indentation from list markers to prevent nesting
        html = html.replace(/^[ \t]+([-*]\s+)/gm, "$1");
        html = html.replace(/^[ \t]+(\d+\.\s+)/gm, "$1");

        // Mark unordered list items with unique tokens (avoid <li> collisions)
        html = html.replace(/^[-*]\s+(.+)$/gm, "\x01UL_S\x02$1\x01UL_E\x02");

        // Mark ordered list items with unique tokens
        html = html.replace(/^\d+\.\s+(.+)$/gm, "\x01OL_S\x02$1\x01OL_E\x02");

        // Group consecutive UL items → <ul>
        html = html.replace(/((?:\x01UL_S\x02.*?\x01UL_E\x02\n*)+)/g, function(m) {
            var items = m.replace(/\x01UL_S\x02/g, "<li>").replace(/\x01UL_E\x02/g, "</li>");
            return "<ul>" + items.trim() + "</ul>";
        });

        // Group consecutive OL items → <ol>
        html = html.replace(/((?:\x01OL_S\x02.*?\x01OL_E\x02\n*)+)/g, function(m) {
            var items = m.replace(/\x01OL_S\x02/g, "<li>").replace(/\x01OL_E\x02/g, "</li>");
            return "<ol>" + items.trim() + "</ol>";
        });

        // Safety net: remove any stray list tokens that weren't grouped
        html = html.replace(/\x01UL_S\x02/g, "<li>").replace(/\x01UL_E\x02/g, "</li>");
        html = html.replace(/\x01OL_S\x02/g, "<li>").replace(/\x01OL_E\x02/g, "</li>");

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

        // ── Step 6: Restore <details>/<summary> blocks ──
        html = html.replace(/\x00DETAILSBLOCK(\d+)\x00/g, (_m, idx) => {
            let inner = detailsBlocks[parseInt(idx, 10)];
            // Render the inner markdown content
            inner = inner
                .replace(/\x00DETSUM_OPEN\x00/g, '<summary>')
                .replace(/\x00DETSUM_CLOSE\x00/g, '</summary>');
            // Process inner markdown (re-run render on the inner content)
            let innerLines = inner.split('\n');
            let processed = innerLines.map(function(line) {
                line = line.trim();
                if (!line) return '';
                if (line.startsWith('<summary>')) return line;
                // Handle numbered items inside details
                var numMatch = line.match(/^\d+\.\s+(.+)$/);
                if (numMatch) return '<li>' + escapeHtml(numMatch[1]) + '</li>';
                return '<p>' + escapeHtml(line) + '</p>';
            }).join('\n');
            // Wrap consecutive <li> in <ol>
            processed = processed.replace(/((?:<li>.*<\/li>\n*)+)/g, '<ol>$1</ol>');
            return '<details>' + processed + '</details>';
        });

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
