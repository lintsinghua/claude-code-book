import './style.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { bookTree, flattenBook, findNodeByPath } from './bookManifest.js';

const STORAGE_THEME_KEY = 'book.reader.theme';
const STORAGE_LAST_PAGE_KEY = 'book.reader.last-page';
const STORAGE_SIDEBAR_COLLAPSED_KEY = 'book.reader.sidebar-collapsed';

const markdownModules = import.meta.glob('/**/*.md', {
  query: '?raw',
  import: 'default'
});

const flatBook = flattenBook(bookTree);

marked.setOptions({
  gfm: true,
  breaks: false
});

const app = document.querySelector('#app');

app.innerHTML = `
  <div class="site-shell">
    <aside class="sidebar">
      <div class="sidebar-top-actions">
        <button id="sidebarToggle" class="icon-btn" type="button" aria-label="收起目录">
          <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </div>

      <div class="brand">
        <p class="brand-kicker">AGENT READING STUDIO</p>
        <h1>Claude Code Book</h1>
      </div>

      <div class="sidebar-actions">
        <div class="search-wrapper">
          <svg viewBox="0 0 24 24"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/></svg>
          <input id="searchInput" type="search" placeholder="筛选章节..." aria-label="筛选章节" />
        </div>
        <button id="themeToggle" class="icon-btn theme-toggle-btn" type="button" aria-label="切换主题">
          <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        </button>
      </div>

      <nav id="bookNav" class="book-nav" aria-label="图书目录"></nav>
    </aside>

    <main class="content">
      <div class="reading-progress" aria-hidden="true">
        <span id="progressBar"></span>
      </div>

      <div class="mobile-header">
        <button id="mobileMenuBtn" class="icon-btn" type="button" aria-label="打开目录">
          <svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
        <span style="font-family: 'ZCOOL XiaoWei', serif; font-weight: 700; color: var(--heading);">Claude Code Book</span>
        <button id="mobileThemeToggle" class="icon-btn theme-toggle-btn" type="button" aria-label="切换主题">
          <svg class="sun-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
        </button>
      </div>

      <div class="content-inner">
        <header class="article-toolbar">
          <div>
            <p class="kicker">正在阅读</p>
            <h2 id="articleTitle">加载中...</h2>
          </div>
          <div class="pager">
            <button id="prevBtn" class="btn-secondary" type="button">
              <svg width="16" height="16" viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>
              上一篇
            </button>
            <button id="nextBtn" class="btn-secondary" type="button">
              下一篇
              <svg width="16" height="16" viewBox="0 0 24 24"><path d="M9 18l6-6-6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>
            </button>
          </div>
        </header>

        <article id="article" class="article markdown-body"></article>
      </div>

      <aside class="toc-panel" aria-label="页内目录">
        <div class="toc-head">
          <p class="toc-title">页内目录</p>
          <button id="tocToggle" class="icon-btn" type="button" aria-label="关闭目录">
            <svg viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        <div id="toc" class="toc"></div>
      </aside>

      <button id="floatingTocBtn" class="floating-toc-btn" aria-label="展开目录">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16M4 12h16M4 18h7"/></svg>
      </button>

    </main>

    <div id="sidebarBackdrop" class="sidebar-backdrop" aria-hidden="true"></div>
  </div>
`;

const elements = {
  nav: document.querySelector('#bookNav'),
  article: document.querySelector('#article'),
  articleTitle: document.querySelector('#articleTitle'),
  searchInput: document.querySelector('#searchInput'),
  themeToggle: [...document.querySelectorAll('.theme-toggle-btn')],
  sidebarToggle: document.querySelector('#sidebarToggle'),
  mobileMenuBtn: document.querySelector('#mobileMenuBtn'),
  sidebarBackdrop: document.querySelector('#sidebarBackdrop'),
  prevBtn: document.querySelector('#prevBtn'),
  nextBtn: document.querySelector('#nextBtn'),
  toc: document.querySelector('#toc'),
  tocToggle: document.querySelector('#tocToggle'),
  floatingTocBtn: document.querySelector('#floatingTocBtn'),
  progressBar: document.querySelector('#progressBar')
};

let currentPath = null;

function isMobileViewport() {
  return window.matchMedia('(max-width: 960px)').matches;
}

function applySidebarCollapsed(collapsed) {
  document.body.classList.toggle('sidebar-collapsed', collapsed);
  localStorage.setItem(STORAGE_SIDEBAR_COLLAPSED_KEY, String(collapsed));
}

function setSidebarOpen(open) {
  document.body.classList.toggle('sidebar-open', open);
}

function initSidebarState() {
  const collapsed = localStorage.getItem(STORAGE_SIDEBAR_COLLAPSED_KEY) === 'true';
  applySidebarCollapsed(collapsed);
}

function normalizePath(path) {
  return path.startsWith('/') ? path : `/${path}`;
}

function renderThemeIcon(isDark) {
  const html = isDark 
    ? `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72l1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>`;
  elements.themeToggle.forEach(btn => btn.innerHTML = html);
}

function applyTheme(theme) {
  const value = theme === 'dark' ? 'dark' : 'light';
  document.documentElement.dataset.theme = value;
  localStorage.setItem(STORAGE_THEME_KEY, value);
  renderThemeIcon(value === 'dark');
}

function initTheme() {
  const stored = localStorage.getItem(STORAGE_THEME_KEY);
  if (stored) {
    applyTheme(stored);
    return;
  }

  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(prefersDark ? 'dark' : 'light');
}

function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\u4e00-\u9fa5\-\s]/g, '')
    .replace(/\s+/g, '-');
}

function renderToc() {
  const headings = [...elements.article.querySelectorAll('h1, h2, h3, h4')];
  if (!headings.length) {
    elements.toc.innerHTML = '<p class="toc-empty">本页暂无目录</p>';
    return;
  }

  elements.toc.innerHTML = `
    <ul>
      ${headings
        .map((heading) => {
          if (!heading.id) {
            heading.id = slugify(heading.textContent || 'section');
          }
          return `<li class="lv-${heading.tagName.toLowerCase()}"><a href="javascript:void(0)" data-target="${heading.id}">${heading.textContent}</a></li>`;
        })
        .join('')}
    </ul>
  `;
}

function updateReadingProgress() {
  const doc = document.documentElement;
  const total = doc.scrollHeight - doc.clientHeight;
  const ratio = total > 0 ? Math.min(1, Math.max(0, window.scrollY / total)) : 0;
  elements.progressBar.style.transform = `scaleX(${ratio})`;
}

function getCurrentIndex() {
  return flatBook.findIndex((item) => item.path === currentPath);
}

function updatePager() {
  const index = getCurrentIndex();
  elements.prevBtn.disabled = index <= 0;
  elements.nextBtn.disabled = index < 0 || index >= flatBook.length - 1;
}

function renderNav(filterText = '') {
  const keyword = filterText.trim().toLowerCase();

  function renderNodes(nodes, level = 0) {
    const items = [];

    for (const node of nodes) {
      if (node.path) {
        const match = !keyword || node.title.toLowerCase().includes(keyword);
        if (!match) continue;
        const isActive = node.path === currentPath;
        items.push(`
          <li>
            <button
              type="button"
              class="nav-item ${isActive ? 'active' : ''}"
              data-path="${node.path}"
              style="--level:${level};"
            >
              ${node.title}
            </button>
          </li>
        `);
      } else {
        const childHtml = renderNodes(node.children || [], level + 1);
        if (!childHtml) continue;
        items.push(`
          <li>
            <p class="group-title" style="--level:${level};">${node.title}</p>
            <ul>${childHtml}</ul>
          </li>
        `);
      }
    }

    return items.join('');
  }

  const html = renderNodes(bookTree);
  elements.nav.innerHTML = html ? `<ul>${html}</ul>` : '<p class="toc-empty" style="margin-left: 12px;">没有匹配章节</p>';
}

async function loadMarkdown(path) {
  const normalized = normalizePath(path);
  const loader = markdownModules[normalized];

  if (!loader) {
    throw new Error(`未找到 Markdown 文件: ${normalized}`);
  }

  const markdown = await loader();
  return markdown;
}

async function openArticle(path, fromHistory = false) {
  currentPath = path;

  const node = findNodeByPath(path);
  elements.articleTitle.textContent = node ? node.title : path;

  elements.article.style.animation = 'none';
  elements.article.offsetHeight; /* trigger reflow */
  elements.article.style.animation = null;

  try {
    const markdown = await loadMarkdown(path);
    const rawHtml = marked.parse(markdown);
    const safeHtml = DOMPurify.sanitize(rawHtml);
    elements.article.innerHTML = safeHtml;
    renderToc();
    renderNav(elements.searchInput.value);
    updatePager();
    updateReadingProgress();

    const hash = `#${encodeURIComponent(path)}`;
    if (!fromHistory && window.location.hash !== hash) {
      history.pushState({ path }, '', hash);
    }

    localStorage.setItem(STORAGE_LAST_PAGE_KEY, path);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (error) {
    elements.article.innerHTML = `<p class="error">加载失败：${error.message}</p>`;
  }
}

function bindEvents() {
  elements.nav.addEventListener('click', (event) => {
    const target = event.target.closest('button[data-path]');
    if (!target) return;

    openArticle(target.dataset.path);
    if (isMobileViewport()) {
      setSidebarOpen(false);
    }
  });

  elements.article.addEventListener('click', (event) => {
    const link = event.target.closest('a');
    if (!link) return;
    
    const href = link.getAttribute('href');
    if (href && href.startsWith('#')) {
      event.preventDefault();
      const targetId = href.substring(1);
      let targetEl = document.getElementById(targetId);
      if (!targetEl) {
        try { targetEl = document.getElementById(decodeURIComponent(targetId)); } catch(e) {}
      }
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  elements.searchInput.addEventListener('input', () => {
    renderNav(elements.searchInput.value);
  });

  elements.themeToggle.forEach(btn => {
    btn.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
    });
  });

  elements.sidebarToggle.addEventListener('click', () => {
    const nextCollapsed = !document.body.classList.contains('sidebar-collapsed');
    applySidebarCollapsed(nextCollapsed);
  });

  if (elements.mobileMenuBtn) {
    elements.mobileMenuBtn.addEventListener('click', () => {
      setSidebarOpen(!document.body.classList.contains('sidebar-open'));
    });
  }

  elements.sidebarBackdrop.addEventListener('click', () => {
    setSidebarOpen(false);
  });

  elements.prevBtn.addEventListener('click', () => {
    const index = getCurrentIndex();
    if (index > 0) openArticle(flatBook[index - 1].path);
  });

  elements.nextBtn.addEventListener('click', () => {
    const index = getCurrentIndex();
    if (index >= 0 && index < flatBook.length - 1) openArticle(flatBook[index + 1].path);
  });

  if (elements.toc) {
    elements.toc.addEventListener('click', (event) => {
      const link = event.target.closest('a[data-target]');
      if (!link) return;
      
      event.preventDefault();
      const targetId = link.getAttribute('data-target');
      if (targetId) {
        let targetEl = document.getElementById(targetId);
        if (!targetEl) {
          try {
            targetEl = document.getElementById(decodeURIComponent(targetId));
          } catch(e) {}
        }
        
        if (targetEl) {
          targetEl.scrollIntoView({ behavior: 'smooth' });
        }
      }
    });
  }

  if (elements.tocToggle) {
    elements.tocToggle.addEventListener('click', () => {
      document.body.classList.add('toc-collapsed');
    });
  }

  if (elements.floatingTocBtn) {
    elements.floatingTocBtn.addEventListener('click', () => {
      document.body.classList.remove('toc-collapsed');
    });
  }

  window.addEventListener('scroll', updateReadingProgress, { passive: true });
  window.addEventListener('resize', () => {
    if (!isMobileViewport()) {
      setSidebarOpen(false);
    }
  });

  window.addEventListener('popstate', (event) => {
    const target = event.state?.path;
    if (target) {
      openArticle(target, true);
      return;
    }

    const fromHash = decodeURIComponent(window.location.hash.replace(/^#/, ''));
    if (fromHash) {
      openArticle(fromHash, true);
    }
  });
}

function resolveInitialPath() {
  const fromHash = decodeURIComponent(window.location.hash.replace(/^#/, ''));
  if (flatBook.some((item) => item.path === fromHash)) return fromHash;

  const lastPage = localStorage.getItem(STORAGE_LAST_PAGE_KEY);
  if (lastPage && flatBook.some((item) => item.path === lastPage)) return lastPage;

  return flatBook[0]?.path;
}

async function bootstrap() {
  initTheme();
  initSidebarState();
  bindEvents();
  renderNav();

  const initialPath = resolveInitialPath();
  if (initialPath) {
    await openArticle(initialPath, true);
  }
}

bootstrap();
