// =========================================================================
// Fresher.AI — Application Core & Presentation Interactivity
// =========================================================================

document.addEventListener('DOMContentLoaded', () => {
  const kb = window.FRESHER_AI_KB || {};
  let currentRoleId = 'role_ai_engineer';
  let currentWeekNumber = 1;
  let currentResourceFilter = 'ALL';
  let currentProjectTierFilter = 'ALL';

  // Role Metadata Configs
  const ROLE_CONFIGS = {
    role_ai_engineer: {
      name: "AI Engineer",
      weeksTotal: 16,
      color: "var(--accent-emerald)",
      title: "AI Engineer Roadmap Progression (16 Weeks)",
      desc: "From Python fundamentals and prompt engineering to building production RAG systems and autonomous LangGraph agents.",
      stages: [
        { num: 1, title: "Python Foundations", bullets: ["Variables & Data Types", "Conditionals & Loops", "Functions, Lists & Dicts"] },
        { num: 2, title: "Python Intermediate", bullets: ["OOP Basics & Classes", "Modules & Imports", "Exception Handling"] },
        { num: 3, title: "Data & APIs", bullets: ["FastAPI REST APIs", "Pydantic Schemas", "Async Python Basics"] },
        { num: 4, title: "LLM Fundamentals", bullets: ["Prompt Engineering", "OpenAI / Claude API", "Structured Outputs"] },
        { num: 5, title: "Vector DBs & RAG", bullets: ["Embeddings & Chunks", "Qdrant Vector Database", "Grounded Citations"] },
        { num: 6, title: "Agents & Workflows", bullets: ["LangGraph StateGraphs", "Tool Calling & Cycles", "Multi-Agent Teams"] },
        { num: 7, title: "Deploy & Evaluate", bullets: ["RAG Triad / Ragas", "Docker Containers", "Cloud Deployment"] }
      ],
      ladder: [
        "Variables / OOP", "REST API & Pydantic", "LLM API Calls", "Embeddings & Vectors", "RAG Pipelines", "LangGraph Agents", "Production RAG"
      ]
    },
    role_full_stack_developer: {
      name: "Full Stack Developer",
      weeksTotal: 12,
      color: "var(--accent-cyan)",
      title: "Full Stack Developer Roadmap Progression (12 Weeks)",
      desc: "From HTML/CSS and TypeScript fundamentals to modern React 18, Next.js 14 App Router, PostgreSQL, and full-stack SaaS deployment.",
      stages: [
        { num: 1, title: "Web Foundations", bullets: ["HTML5 & CSS Grid/Flexbox", "Responsive Layouts", "Git & GitHub Workflow"] },
        { num: 2, title: "JavaScript & TS", bullets: ["ES6+ & Async/Await", "TypeScript Strict Types", "DOM Manipulation"] },
        { num: 3, title: "React Essentials", bullets: ["JSX & Components", "useState & useEffect", "Component Lifecycle"] },
        { num: 4, title: "Next.js App Router", bullets: ["Server Components", "Client Components", "File-based Routing & SSR"] },
        { num: 5, title: "Backend & Databases", bullets: ["Node.js & Express", "PostgreSQL & SQL Queries", "Prisma ORM Migrations"] },
        { num: 6, title: "Auth & Payments", bullets: ["NextAuth / Clerk Auth", "Stripe Webhooks", "Protected Routes"] },
        { num: 7, title: "Full Stack Capstone", bullets: ["Multi-Tenant SaaS", "Docker Compose Stack", "Vercel & Render Deploy"] }
      ],
      ladder: [
        "HTML/CSS/JS", "TypeScript Strict", "React Components", "Next.js App Router", "Postgres & Prisma", "Auth & Billing", "Production SaaS"
      ]
    },
    role_devops_engineer: {
      name: "DevOps Engineer",
      weeksTotal: 12,
      color: "var(--accent-purple)",
      title: "DevOps Engineer Roadmap Progression (12 Weeks)",
      desc: "From Linux terminal commands and Bash scripting to Docker, Kubernetes clustering, Terraform IaC, and GitHub Actions CI/CD pipelines.",
      stages: [
        { num: 1, title: "Linux & Bash", bullets: ["File Hierarchy & Perms", "Process Inspection", "Bash Script Automation"] },
        { num: 2, title: "Networking & Security", bullets: ["TCP/IP, DNS, HTTP/HTTPS", "SSH Keys & Hardening", "UFW & Firewalls"] },
        { num: 3, title: "Git & Web Servers", bullets: ["Git Branching Strategies", "Nginx Reverse Proxy", "SSL/TLS Certbot"] },
        { num: 4, title: "Containers & Docker", bullets: ["Multi-Stage Dockerfiles", "Image Optimization", "Docker Compose Services"] },
        { num: 5, title: "CI/CD Automation", bullets: ["GitHub Actions Workflows", "Automated Lint & Test", "Container Registry Push"] },
        { num: 6, title: "Kubernetes & IaC", bullets: ["Pods, Deployments, Services", "ConfigMaps & Ingress", "Terraform AWS Modules"] },
        { num: 7, title: "Monitoring & Capstone", bullets: ["Prometheus Metrics", "Grafana Dashboards", "End-to-End GitOps Pipeline"] }
      ],
      ladder: [
        "Linux CLI / Bash", "Networking / SSH", "Nginx & SSL", "Docker Containers", "GitHub Actions CI", "Kubernetes / Terraform", "Prometheus GitOps"
      ]
    }
  };

  // UI Element Selectors
  const roleTabs = document.querySelectorAll('.role-tab');
  const viewNavTabs = document.querySelectorAll('.nav-tab');
  const slideSections = document.querySelectorAll('.slide-section');

  // Slide 1 Elements
  const stageProgressionTitle = document.getElementById('stageProgressionTitle');
  const stageProgressionDesc = document.getElementById('stageProgressionDesc');
  const stageCardsGrid = document.getElementById('stageCardsGrid');
  const ladderSteps = document.getElementById('ladderSteps');

  // Slide 2 Elements
  const weekButtonsList = document.getElementById('weekButtonsList');
  const weekCountBadge = document.getElementById('weekCountBadge');
  const weekDetailContent = document.getElementById('weekDetailContent');

  // Slide 3 Elements
  const categoriesContainer = document.getElementById('categoriesContainer');
  const purposeFilters = document.getElementById('purposeFilters');
  const resourceSearchInput = document.getElementById('resourceSearchInput');

  // Slide 4 Elements
  const projectsGrid = document.getElementById('projectsGrid');
  const projectTierTabs = document.getElementById('projectTierTabs');
  const totalProjCount = document.getElementById('totalProjCount');
  const starterProjCount = document.getElementById('starterProjCount');
  const interProjCount = document.getElementById('interProjCount');
  const capstoneProjCount = document.getElementById('capstoneProjCount');

  // Slide 5 Elements
  const youtubeSectionsWrapper = document.getElementById('youtubeSectionsWrapper');

  // Modal Elements
  const appModal = document.getElementById('appModal');
  const modalBackdrop = document.getElementById('modalBackdrop');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalBody = document.getElementById('modalBody');

  // =========================================================================
  // Initialize Application
  // =========================================================================
  function init() {
    bindEventListeners();
    renderAllViews();
  }

  function bindEventListeners() {
    // Role Switching
    roleTabs.forEach(btn => {
      btn.addEventListener('click', () => {
        roleTabs.forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        currentRoleId = btn.dataset.role;
        currentWeekNumber = 1;
        renderAllViews();
      });
    });

    // View Nav Switching
    viewNavTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        viewNavTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const targetViewId = 'view-' + tab.dataset.view;
        slideSections.forEach(sec => {
          sec.classList.toggle('active', sec.id === targetViewId);
        });
      });
    });

    // Resource Purpose Filters
    if (purposeFilters) {
      purposeFilters.addEventListener('click', (e) => {
        if (e.target.classList.contains('filter-pill')) {
          purposeFilters.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
          e.target.classList.add('active');
          currentResourceFilter = e.target.dataset.purpose;
          renderResourcesView();
        }
      });
    }

    // Resource Search
    if (resourceSearchInput) {
      resourceSearchInput.addEventListener('input', () => {
        renderResourcesView();
      });
    }

    // Project Tier Filters
    if (projectTierTabs) {
      projectTierTabs.addEventListener('click', (e) => {
        if (e.target.classList.contains('tier-tab')) {
          projectTierTabs.querySelectorAll('.tier-tab').forEach(t => t.classList.remove('active'));
          e.target.classList.add('active');
          currentProjectTierFilter = e.target.dataset.tier;
          renderProjectsView();
        }
      });
    }

    // Modal Close
    modalBackdrop.addEventListener('click', closeModal);
    modalCloseBtn.addEventListener('click', closeModal);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
  }

  function renderAllViews() {
    renderStageProgressionView();
    renderWeeklySidebar();
    renderWeekDetail();
    renderResourcesView();
    renderProjectsView();
    renderYouTubeView();
  }

  // =========================================================================
  // SLIDE 1: 7-Stage Progression View
  // =========================================================================
  function renderStageProgressionView() {
    const config = ROLE_CONFIGS[currentRoleId] || ROLE_CONFIGS.role_ai_engineer;
    stageProgressionTitle.textContent = config.title;
    stageProgressionDesc.textContent = config.desc;

    // Render Stage Cards
    stageCardsGrid.innerHTML = config.stages.map(st => `
      <div class="stage-card">
        <div class="stage-number">${st.num}</div>
        <h3 class="stage-title">${st.title}</h3>
        <ul class="stage-bullets">
          ${st.bullets.map(b => `<li>${b}</li>`).join('')}
        </ul>
      </div>
    `).join('');

    // Render Conceptual Ladder
    ladderSteps.innerHTML = config.ladder.map((step, idx) => `
      <div class="ladder-step">${step}</div>
      ${idx < config.ladder.length - 1 ? '<span class="ladder-arrow">→</span>' : ''}
    `).join('');
  }

  // =========================================================================
  // SLIDE 2: Weekly Guide ("Do This Next") View
  // =========================================================================
  function getRoadmapsForRole(roleId) {
    const roadmaps = kb.weekly_roadmaps || [];
    return roadmaps.filter(rm => rm.role_id === roleId).sort((a, b) => a.week_number - b.week_number);
  }

  function renderWeeklySidebar() {
    const roadmaps = getRoadmapsForRole(currentRoleId);
    weekCountBadge.textContent = `${roadmaps.length} Weeks`;

    weekButtonsList.innerHTML = roadmaps.map(rm => `
      <button class="week-nav-btn ${rm.week_number === currentWeekNumber ? 'active' : ''}" data-week="${rm.week_number}">
        <span><span class="week-nav-num">W${rm.week_number}</span> ${escapeHtml(rm.phase_name)}</span>
        <span class="meta-pill pill-difficulty-${rm.difficulty || 'beginner'}">${(rm.difficulty || 'beg').slice(0,3).toUpperCase()}</span>
      </button>
    `).join('');

    // Attach click handlers
    weekButtonsList.querySelectorAll('.week-nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        currentWeekNumber = parseInt(btn.dataset.week, 10);
        weekButtonsList.querySelectorAll('.week-nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderWeekDetail();
      });
    });
  }

  function renderWeekDetail() {
    const roadmaps = getRoadmapsForRole(currentRoleId);
    const rm = roadmaps.find(r => r.week_number === currentWeekNumber) || roadmaps[0];
    if (!rm) {
      weekDetailContent.innerHTML = `<p>No roadmap data available for this week.</p>`;
      return;
    }

    // Lookup linked items
    const allResources = kb.resources || [];
    const allYT = kb.youtube_channels || [];
    const allTools = kb.tools_platforms || [];
    const allProjects = kb.projects || [];

    // Find primary resource
    const recResId = (rm.recommended_resource_ids || '').split(';')[0]?.trim();
    const primaryResource = allResources.find(r => r.resource_id === recResId) || allResources[0];

    // Find primary YouTube
    const recYtId = (rm.recommended_youtube_ids || '').split(';')[0]?.trim();
    const primaryYT = allYT.find(y => y.channel_id === recYtId) || allYT[0];

    // Find primary Tool
    const recToolId = (rm.recommended_tool_ids || '').split(';')[0]?.trim();
    const primaryTool = allTools.find(t => t.tool_id === recToolId) || allTools[0];

    // Find primary Project
    const recProjId = (rm.recommended_project_ids || '').split(';')[0]?.trim();
    const primaryProj = allProjects.find(p => p.project_id === recProjId) || allProjects.find(p => p.role_id === currentRoleId);

    // Parse Daily Breakdown (Day 1..7)
    const dailyText = rm.daily_breakdown || '';
    const dayRegex = /(Day\s*\d+[^:]*):?\s*([^;]+)/gi;
    const days = [];
    let match;
    while ((match = dayRegex.exec(dailyText)) !== null) {
      days.push({ day: match[1].trim(), desc: match[2].trim() });
    }
    if (days.length === 0) {
      days.push({ day: "Days 1-3", desc: "Core syntax fundamentals and official documentation reading." });
      days.push({ day: "Days 4-5", desc: "Practical hands-on code exercises and tool setup." });
      days.push({ day: "Days 6-7", desc: "Build weekly milestone deliverable and push to GitHub." });
    }

    weekDetailContent.innerHTML = `
      <!-- Week Overview Card -->
      <div class="week-detail-header">
        <div class="week-meta-pills">
          <span class="meta-pill pill-difficulty-${rm.difficulty || 'beginner'}">${(rm.difficulty || 'beginner').toUpperCase()}</span>
          <span class="meta-pill pill-hours">~${rm.estimated_hours || 15} Hours</span>
          <span class="meta-pill" style="background: rgba(168, 85, 247, 0.15); color: var(--accent-purple);">Week ${rm.week_number} of ${roadmaps.length}</span>
        </div>
        <h2 class="week-title">${escapeHtml(rm.phase_name)}</h2>
        <p class="week-goal"><strong>Weekly Goal:</strong> ${escapeHtml(rm.weekly_goal || '')}</p>
      </div>

      <!-- Recommendation Hierarchy: "DO THIS NEXT" -->
      <div class="action-path-container">
        <!-- 1. Start Here -->
        <div class="action-card">
          <div class="action-card-header">
            <span class="action-step-tag">STEP 1</span>
            <span class="action-title">Start Here (Docs)</span>
          </div>
          <div class="action-resource-item">
            <h4>${escapeHtml(primaryResource?.title || 'Official Documentation')}</h4>
            <p>${escapeHtml(primaryResource?.best_for || primaryResource?.description || 'Read official docs to build mental models.')}</p>
            ${primaryResource?.url ? `<a href="${primaryResource.url}" target="_blank" class="action-btn-link">Open Official Guide ↗</a>` : ''}
          </div>
        </div>

        <!-- 2. Then Watch -->
        <div class="action-card">
          <div class="action-card-header">
            <span class="action-step-tag">STEP 2</span>
            <span class="action-title">Then Watch (YouTube)</span>
          </div>
          <div class="action-resource-item">
            <h4>${escapeHtml(primaryYT?.channel_name || 'Recommended Channel')}</h4>
            <p>${escapeHtml(primaryYT?.best_for || primaryYT?.recommended_use || 'Watch curated video walkthroughs.')}</p>
            ${primaryYT?.url ? `<a href="${primaryYT.url}" target="_blank" class="action-btn-link">Watch on YouTube ↗</a>` : ''}
          </div>
        </div>

        <!-- 3. Then Use -->
        <div class="action-card">
          <div class="action-card-header">
            <span class="action-step-tag">STEP 3</span>
            <span class="action-title">Then Use (Tool)</span>
          </div>
          <div class="action-resource-item">
            <h4>${escapeHtml(primaryTool?.tool_name || 'Development Tool')}</h4>
            <p>${escapeHtml(primaryTool?.purpose || primaryTool?.best_for || 'Install and configure your toolchain.')}</p>
            ${primaryTool?.website_url ? `<a href="${primaryTool.website_url}" target="_blank" class="action-btn-link">Get Tool ↗</a>` : ''}
          </div>
        </div>

        <!-- 4. Then Build -->
        <div class="action-card">
          <div class="action-card-header">
            <span class="action-step-tag">STEP 4</span>
            <span class="action-title">Then Build (Project)</span>
          </div>
          <div class="action-resource-item">
            <h4>${escapeHtml(primaryProj?.title || rm.hands_on_deliverable || 'Hands-On Deliverable')}</h4>
            <p>${escapeHtml(primaryProj?.description || rm.weekly_goal || 'Write real code and commit to GitHub.')}</p>
            ${primaryProj ? `<button class="action-btn-link view-proj-btn" data-projid="${primaryProj.project_id}" style="background:none;border:none;cursor:pointer;">View Architecture ↗</button>` : ''}
          </div>
        </div>
      </div>

      <!-- 7-Day Structured Daily Schedule -->
      <div class="daily-schedule-card">
        <h3><span>📅</span> 7-Day Execution Blueprint</h3>
        <div class="days-grid">
          ${days.map(d => `
            <div class="day-item">
              <div class="day-item-header">${escapeHtml(d.day)}</div>
              <div class="day-item-text">${escapeHtml(d.desc)}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- Learning Outcomes & Interview Prep -->
      <div class="outcomes-grid">
        <div class="outcome-card">
          <h4><span>🎯</span> Verified Learning Outcomes</h4>
          <p>${escapeHtml(rm.learning_outcomes || 'Master core weekly competencies.')}</p>
        </div>
        <div class="outcome-card">
          <h4><span>💡</span> Interview Prep & Resume Evidence</h4>
          <p><strong>Topics:</strong> ${escapeHtml(rm.interview_topics || '')}</p>
          <p style="margin-top:6px;"><strong>Resume Bullet:</strong> ${escapeHtml(rm.resume_evidence || '')}</p>
        </div>
      </div>
    `;

    // Modal click listeners
    weekDetailContent.querySelectorAll('.view-proj-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        openProjectModal(btn.dataset.projid);
      });
    });
  }

  // =========================================================================
  // SLIDE 3: Resource Ecosystem View (5 Sections + 9 Purpose Badges)
  // =========================================================================
  function renderResourcesView() {
    const resources = kb.resources || [];
    const query = (resourceSearchInput?.value || '').toLowerCase().trim();

    // 5 Defined Visual Sections
    const SECTIONS = [
      { id: "Developer Essentials", title: "Developer Essentials & Fundamentals", icon: "⚡" },
      { id: "Backend & Infrastructure", title: "Backend, Databases & Infrastructure", icon: "🗄️" },
      { id: "AI Engineering", title: "AI Engineering & Vector Intelligence", icon: "🧠" },
      { id: "Learning & Practice", title: "Interactive Practice & Learning Roadmaps", icon: "🎯" },
      { id: "Career & Jobs", title: "Career Readiness, Portfolios & Jobs", icon: "💼" }
    ];

    // Filter resources
    const filtered = resources.filter(res => {
      // Purpose filter
      if (currentResourceFilter !== 'ALL' && res.resource_purpose !== currentResourceFilter) {
        return false;
      }
      // Search query filter
      if (query) {
        const text = `${res.title} ${res.category} ${res.resource_purpose} ${res.best_for} ${res.description}`.toLowerCase();
        return text.includes(query);
      }
      return true;
    });

    // Group by 5 UI categories
    categoriesContainer.innerHTML = SECTIONS.map(sec => {
      const items = filtered.filter(r => r.category === sec.id);
      if (items.length === 0) return '';

      return `
        <div class="category-group">
          <div class="category-group-header">
            <span>${sec.icon}</span>
            <h2>${sec.title}</h2>
            <span class="category-badge-count">${items.length}</span>
          </div>
          <div class="resource-cards-grid">
            ${items.map(res => `
              <div class="resource-card">
                <div class="resource-card-top">
                  <span class="purpose-badge">${escapeHtml(res.resource_purpose || 'LEARN')}</span>
                  <span class="meta-pill pill-difficulty-${res.difficulty || 'beginner'}">${(res.difficulty || 'beg').toUpperCase()}</span>
                </div>
                <h3 class="resource-name">${escapeHtml(res.title)}</h3>
                <div class="resource-best-for">${escapeHtml(res.best_for || '')}</div>
                <p class="resource-description">${escapeHtml(res.description || '')}</p>
                <div class="resource-card-footer">
                  <span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(res.provider || '')}</span>
                  <a href="${res.url}" target="_blank" class="open-resource-btn">Open Link ↗</a>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }).join('');

    if (categoriesContainer.innerHTML.trim() === '') {
      categoriesContainer.innerHTML = `<p style="text-align:center;color:var(--text-muted);padding:40px;">No resources found matching filter criteria.</p>`;
    }
  }

  // =========================================================================
  // SLIDE 4: Sequenced Projects View (1..N Progression)
  // =========================================================================
  function renderProjectsView() {
    const projects = kb.projects || [];
    const roleProjects = projects
      .filter(p => p.role_id === currentRoleId)
      .sort((a, b) => (a.project_sequence || 0) - (b.project_sequence || 0));

    // Update Counts
    const starters = roleProjects.filter(p => p.tier === 'starter');
    const intermediates = roleProjects.filter(p => p.tier === 'intermediate');
    const capstones = roleProjects.filter(p => p.tier === 'capstone');

    if (totalProjCount) totalProjCount.textContent = roleProjects.length;
    if (starterProjCount) starterProjCount.textContent = starters.length;
    if (interProjCount) interProjCount.textContent = intermediates.length;
    if (capstoneProjCount) capstoneProjCount.textContent = capstones.length;

    // Filter by tier
    const filtered = roleProjects.filter(p => {
      if (currentProjectTierFilter === 'ALL') return true;
      return p.tier === currentProjectTierFilter;
    });

    projectsGrid.innerHTML = filtered.map(p => `
      <div class="project-card">
        <div class="project-header-row">
          <span class="project-seq-badge">#${p.project_sequence || 1}</span>
          <span class="project-tier-pill tier-${p.tier || 'starter'}">${(p.tier || 'starter').toUpperCase()}</span>
        </div>
        <h3 class="project-card-title">${escapeHtml(p.title)}</h3>
        <div class="project-tech-stack">${escapeHtml(p.tech_stack || '')}</div>
        <p class="project-desc">${escapeHtml(p.description || '')}</p>
        
        <div class="project-resume-box">
          <strong>Resume Bullet:</strong><br>
          ${escapeHtml(p.resume_bullet_point || '')}
        </div>

        <div class="project-card-actions">
          <span style="font-size:0.75rem; color:var(--text-muted);">Week ${p.recommended_week || 1} • ~${p.estimated_hours || 10} hrs</span>
          <button class="project-btn-details" data-projid="${p.project_id}">Architecture Details</button>
        </div>
      </div>
    `).join('');

    // Attach modal buttons
    projectsGrid.querySelectorAll('.project-btn-details').forEach(btn => {
      btn.addEventListener('click', () => {
        openProjectModal(btn.dataset.projid);
      });
    });
  }

  // =========================================================================
  // SLIDE 5: Curated YouTube View (Priority vs Additional)
  // =========================================================================
  function renderYouTubeView() {
    const channels = kb.youtube_channels || [];
    
    // Filter relevant channels for role or general
    const roleChannels = channels.filter(ch => {
      const roles = ch.role_ids || '';
      return roles.includes(currentRoleId) || roles.includes('role_all') || !roles;
    });

    const priorityChannels = roleChannels.filter(c => c.priority === true);
    const additionalChannels = roleChannels.filter(c => !c.priority);

    const playlists = kb.Playlists || kb.playlists || [];
    
    youtubeSectionsWrapper.innerHTML = `
      <!-- Priority Educators -->
      <div class="yt-group">
        <h3 class="youtube-section-title"><span>⭐</span> Primary Recommended Educators (India & Global)</h3>
        <div class="yt-cards-grid">
          ${priorityChannels.map(ch => renderYouTubeCard(ch, true)).join('')}
        </div>
      </div>

      <!-- Curated Topic Playlists -->
      ${playlists.length > 0 ? `
        <div class="yt-group" style="margin-top: 32px;">
          <h3 class="youtube-section-title"><span>📑</span> Curated Playlists & Roadmaps</h3>
          <div class="yt-cards-grid">
            ${playlists.map(pl => `
              <div class="yt-card" style="border-left: 3px solid var(--accent-orange);">
                <div class="yt-card-header">
                  <div>
                    <h4 class="yt-name" style="font-size: 1.05rem;">${escapeHtml(pl.playlist_name)}</h4>
                    <span class="yt-handle">${escapeHtml(pl.channel_name)} • ${escapeHtml(pl.skill_area)}</span>
                  </div>
                  <span class="purpose-badge" style="background: rgba(249, 115, 22, 0.15); color: var(--accent-orange);">${escapeHtml(pl.role_area)}</span>
                </div>
                <div class="yt-card-footer" style="margin-top: 12px; padding-top: 8px;">
                  <span style="font-size:0.75rem; color:var(--text-muted);">${escapeHtml(pl.language)}</span>
                  <a href="${pl.url}" target="_blank" class="open-resource-btn">Open Playlist ↗</a>
                </div>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Additional Specialized Channels -->
      ${additionalChannels.length > 0 ? `
        <div class="yt-group" style="margin-top: 32px;">
          <h3 class="youtube-section-title"><span>📺</span> Additional Specialized & Deep-Dive Channels</h3>
          <div class="yt-cards-grid">
            ${additionalChannels.map(ch => renderYouTubeCard(ch, false)).join('')}
          </div>
        </div>
      ` : ''}
    `;
  }

  function renderYouTubeCard(ch, isPriority) {
    return `
      <div class="yt-card">
        <div class="yt-card-header">
          <div>
            <h4 class="yt-name">${escapeHtml(ch.channel_name)}</h4>
            <span class="yt-handle">${escapeHtml(ch.handle || '')}</span>
          </div>
          ${isPriority ? `<span class="yt-badge-priority">TOP PICK</span>` : ''}
        </div>
        <div class="yt-best-for">${escapeHtml(ch.best_for || '')}</div>
        <p class="yt-rec-use"><strong>How to Use:</strong> ${escapeHtml(ch.recommended_use || '')}</p>
        <div class="yt-card-footer">
          <span style="font-size:0.75rem; color:var(--text-muted);">${ch.language || 'English'}</span>
          <a href="${ch.url}" target="_blank" class="open-resource-btn">Visit Channel ↗</a>
        </div>
      </div>
    `;
  }

  // =========================================================================
  // Modal Popups for Deep Dive
  // =========================================================================
  function openProjectModal(projectId) {
    const projects = kb.projects || [];
    const p = projects.find(proj => proj.project_id === projectId);
    if (!p) return;

    modalBody.innerHTML = `
      <div style="margin-bottom: 20px;">
        <span class="editorial-badge">PROJECT ARCHITECTURE DEEP-DIVE</span>
        <h2 style="font-size: 1.6rem; margin-top: 8px;">#${p.project_sequence || 1}: ${escapeHtml(p.title)}</h2>
        <p style="color: var(--accent-cyan); font-family: var(--font-code); font-size: 0.85rem; margin-top: 4px;">
          Tech Stack: ${escapeHtml(p.tech_stack || '')}
        </p>
      </div>

      <div style="display: flex; flex-direction: column; gap: 16px;">
        <div style="background: var(--bg-surface); padding: 16px; border-radius: var(--radius-md);">
          <h4 style="color: #FFFFFF; font-size: 0.95rem; margin-bottom: 6px;">📐 Architecture Summary</h4>
          <p style="font-family: var(--font-code); font-size: 0.85rem; color: var(--accent-orange);">
            ${escapeHtml(p.architecture_summary || 'Multi-tier modular architecture')}
          </p>
        </div>

        <div style="background: var(--bg-surface); padding: 16px; border-radius: var(--radius-md);">
          <h4 style="color: #FFFFFF; font-size: 0.95rem; margin-bottom: 6px;">🎯 What You Will Learn</h4>
          <p style="font-size: 0.85rem; color: var(--text-secondary);">
            ${escapeHtml(p.what_you_will_learn || p.learning_objectives || '')}
          </p>
        </div>

        <div style="background: var(--bg-surface); padding: 16px; border-radius: var(--radius-md);">
          <h4 style="color: #FFFFFF; font-size: 0.95rem; margin-bottom: 6px;">⚙️ Key Features & Deliverables</h4>
          <p style="font-size: 0.85rem; color: var(--text-secondary);">
            <strong>Features:</strong> ${escapeHtml(p.features_to_build || p.key_features || '')}<br>
            <strong>Deliverables:</strong> ${escapeHtml(p.deliverables || 'GitHub repo + Live Deployment')}
          </p>
        </div>

        <div style="background: var(--bg-surface); padding: 16px; border-radius: var(--radius-md);">
          <h4 style="color: #FFFFFF; font-size: 0.95rem; margin-bottom: 6px;">📝 Resume Bullet Point</h4>
          <p style="font-size: 0.85rem; color: #E2E8F0; border-left: 2px solid var(--accent-purple); padding-left: 10px;">
            ${escapeHtml(p.resume_bullet_point || '')}
          </p>
        </div>

        ${p.github_template_url ? `
          <div style="margin-top: 8px;">
            <a href="${p.github_template_url}" target="_blank" style="display:inline-block; background:var(--accent-purple); color:#FFFFFF; padding:10px 20px; border-radius:var(--radius-pill); font-weight:600; font-size:0.85rem;">
              View GitHub Starter Template ↗
            </a>
          </div>
        ` : ''}
      </div>
    `;

    appModal.classList.add('active');
  }

  function closeModal() {
    appModal.classList.remove('active');
  }

  // Security Helper
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Run app
  init();
});
