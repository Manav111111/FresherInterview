import {
  FiPlus,
  FiTrash2,
  FiUser,
  FiMail,
  FiPhone,
  FiMapPin,
  FiLinkedin,
  FiGithub,
  FiBookOpen,
  FiAward,
  FiCalendar,
  FiBriefcase,
  FiCode,
  FiFolder,
  FiGlobe,
  FiFileText
} from "react-icons/fi";

// ─── Input with Left Squircle Icon ────────────────────────────────────────────
function InputWithIcon({ icon: Icon, label, value, onChange, placeholder, type = "text" }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-slate-700">
        {label}
      </label>
      <div className="flex items-center gap-2.5">
        {Icon && (
          <div className="w-11 h-11 rounded-2xl bg-indigo-50/70 border border-indigo-100/70 text-indigo-600 flex items-center justify-center shrink-0 shadow-2xs">
            <Icon size={16} />
          </div>
        )}
        <input
          type={type}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="flex-1 h-11 rounded-2xl bg-slate-50/80 border border-slate-200/80 px-4 text-xs sm:text-sm font-medium text-slate-800 outline-none focus:bg-white focus:border-indigo-500 transition placeholder:text-slate-400"
        />
      </div>
    </div>
  );
}

// ─── Standard Form Input ──────────────────────────────────────────────────────
function FormInput({ label, value, onChange, placeholder, type = "text" }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-slate-700">
        {label}
      </label>
      <input
        type={type}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full h-11 rounded-2xl bg-slate-50/80 border border-slate-200/80 px-4 text-xs sm:text-sm font-medium text-slate-800 outline-none focus:bg-white focus:border-indigo-500 transition placeholder:text-slate-400"
      />
    </div>
  );
}

// ─── Reusable Textarea ────────────────────────────────────────────────────────
function FormTextarea({ label, value, onChange, placeholder, rows = 4 }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-semibold text-slate-700">
        {label}
      </label>
      <textarea
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full rounded-2xl bg-slate-50/80 border border-slate-200/80 p-4 text-xs sm:text-sm font-medium text-slate-800 outline-none focus:bg-white focus:border-indigo-500 transition placeholder:text-slate-400 resize-none leading-relaxed"
      />
    </div>
  );
}

// ─── Add / Remove Entry Card ──────────────────────────────────────────────────
function EntryCard({ title, onRemove, children }) {
  return (
    <div className="relative bg-slate-50/60 border border-slate-200/80 rounded-2xl p-5 space-y-3.5 transition-all">
      <div className="flex items-center justify-between pb-2 border-b border-slate-200/60">
        <span className="text-xs font-bold text-slate-700">{title}</span>
        <button
          type="button"
          onClick={onRemove}
          className="text-slate-400 hover:text-rose-500 hover:bg-rose-50 p-1.5 rounded-lg transition-colors cursor-pointer"
        >
          <FiTrash2 size={14} />
        </button>
      </div>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

// ─── Main ResumeForm Component ────────────────────────────────────────────────
export default function ResumeForm({ step, data, setData }) {

  // ── Step 1: Personal Info ──────────────────────────────────────────────────
  if (step === 1) {
    return (
      <div className="space-y-3.5">
        <InputWithIcon
          icon={FiUser}
          label="Full Name"
          value={data.name}
          onChange={(v) => setData({ ...data, name: v })}
          placeholder="Rahul Sharma"
        />
        <InputWithIcon
          icon={FiMail}
          label="Email Address"
          value={data.email}
          onChange={(v) => setData({ ...data, email: v })}
          placeholder="rahul@email.com"
        />
        <InputWithIcon
          icon={FiPhone}
          label="Phone Number"
          value={data.phone}
          onChange={(v) => setData({ ...data, phone: v })}
          placeholder="+91 9876543210"
        />
        <InputWithIcon
          icon={FiMapPin}
          label="Location"
          value={data.location}
          onChange={(v) => setData({ ...data, location: v })}
          placeholder="Jhansi, UP"
        />
        <InputWithIcon
          icon={FiLinkedin}
          label="LinkedIn URL"
          value={data.linkedin}
          onChange={(v) => setData({ ...data, linkedin: v })}
          placeholder="linkedin.com/in/rahul"
        />
        <InputWithIcon
          icon={FiGithub}
          label="GitHub URL"
          value={data.github}
          onChange={(v) => setData({ ...data, github: v })}
          placeholder="github.com/rahul"
        />
      </div>
    );
  }

  // ── Step 2: Education ──────────────────────────────────────────────────────
  if (step === 2) {
    const addEdu = () => {
      setData({
        ...data,
        education: [
          ...(data.education || []),
          { college: "", degree: "", branch: "", cgpa: "", year: "" },
        ],
      });
    };

    const updateEdu = (index, field, value) => {
      const updated = data.education.map((edu, i) =>
        i === index ? { ...edu, [field]: value } : edu
      );
      setData({ ...data, education: updated });
    };

    const removeEdu = (index) => {
      setData({ ...data, education: data.education.filter((_, i) => i !== index) });
    };

    return (
      <div className="space-y-4">
        {(data.education || []).length === 0 && (
          <div className="text-center py-6 text-slate-400 space-y-1">
            <p className="text-xs font-semibold">No education details added yet.</p>
            <p className="text-[11px]">Click the button below to add your degree or college.</p>
          </div>
        )}

        {(data.education || []).map((edu, index) => (
          <EntryCard
            key={index}
            title={`Education #${index + 1}`}
            onRemove={() => removeEdu(index)}
          >
            <FormInput
              label="College / University"
              value={edu.college}
              onChange={(v) => updateEdu(index, "college", v)}
              placeholder="SR Group of Institutions, Jhansi"
            />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormInput
                label="Degree"
                value={edu.degree}
                onChange={(v) => updateEdu(index, "degree", v)}
                placeholder="B.Tech"
              />
              <FormInput
                label="Branch / Specialization"
                value={edu.branch}
                onChange={(v) => updateEdu(index, "branch", v)}
                placeholder="Computer Science & Engineering"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormInput
                label="CGPA / Percentage"
                value={edu.cgpa}
                onChange={(v) => updateEdu(index, "cgpa", v)}
                placeholder="8.5 / 10"
              />
              <FormInput
                label="Graduation Year"
                value={edu.year}
                onChange={(v) => updateEdu(index, "year", v)}
                placeholder="2021 – 2025"
              />
            </div>
          </EntryCard>
        ))}

        <button
          type="button"
          onClick={addEdu}
          className="w-full py-3 rounded-2xl border-2 border-dashed border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <FiPlus size={15} />
          <span>Add Education</span>
        </button>
      </div>
    );
  }

  // ── Step 3: Experience ─────────────────────────────────────────────────────
  if (step === 3) {
    const addExp = () => {
      setData({
        ...data,
        experience: [
          ...(data.experience || []),
          { company: "", role: "", duration: "", description: "" },
        ],
      });
    };

    const updateExp = (index, field, value) => {
      const updated = data.experience.map((exp, i) =>
        i === index ? { ...exp, [field]: value } : exp
      );
      setData({ ...data, experience: updated });
    };

    const removeExp = (index) => {
      setData({ ...data, experience: data.experience.filter((_, i) => i !== index) });
    };

    return (
      <div className="space-y-4">
        {(data.experience || []).length === 0 && (
          <div className="text-center py-6 text-slate-400 space-y-1">
            <p className="text-xs font-semibold">No work experience or internships added yet.</p>
            <p className="text-[11px]">You can add internships, part-time roles, or skip to projects.</p>
          </div>
        )}

        {(data.experience || []).map((exp, index) => (
          <EntryCard
            key={index}
            title={`Experience #${index + 1}`}
            onRemove={() => removeExp(index)}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormInput
                label="Company Name"
                value={exp.company}
                onChange={(v) => updateExp(index, "company", v)}
                placeholder="Google / Startup Labs"
              />
              <FormInput
                label="Job Title / Role"
                value={exp.role}
                onChange={(v) => updateExp(index, "role", v)}
                placeholder="Software Engineering Intern"
              />
            </div>
            <FormInput
              label="Duration"
              value={exp.duration}
              onChange={(v) => updateExp(index, "duration", v)}
              placeholder="Jan 2024 – Jun 2024"
            />
            <FormTextarea
              label="Key Responsibilities & Impact"
              value={exp.description}
              onChange={(v) => updateExp(index, "description", v)}
              placeholder="• Engineered REST microservices in Node.js and reduced query latency by 35%&#10;• Integrated Redis caching layer for high-throughput user authentication"
              rows={4}
            />
          </EntryCard>
        ))}

        <button
          type="button"
          onClick={addExp}
          className="w-full py-3 rounded-2xl border-2 border-dashed border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <FiPlus size={15} />
          <span>Add Experience</span>
        </button>
      </div>
    );
  }

  // ── Step 4: Skills ─────────────────────────────────────────────────────────
  if (step === 4) {
    const quickSuggestions = [
      "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "Express",
      "Python", "FastAPI", "PostgreSQL", "MongoDB", "Redis", "Docker",
      "Git", "REST APIs", "Data Structures & Algorithms", "Tailwind CSS"
    ];

    const addSkill = (skill) => {
      const current = data.skills ? data.skills.split(",").map((s) => s.trim()) : [];
      if (!current.includes(skill)) {
        const next = current.filter(Boolean).concat(skill).join(", ");
        setData({ ...data, skills: next });
      }
    };

    return (
      <div className="space-y-4">
        <FormTextarea
          label="Technical Skills (Comma separated)"
          value={data.skills}
          onChange={(v) => setData({ ...data, skills: v })}
          placeholder="Java, Python, React, Node.js, Express, MongoDB, Redis, Docker, Git, RESTful APIs, DSA"
          rows={5}
        />

        {/* Quick Suggestion Pills */}
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            Popular Skill Suggestions (Click to add):
          </p>
          <div className="flex flex-wrap gap-1.5">
            {quickSuggestions.map((skill) => (
              <button
                key={skill}
                type="button"
                onClick={() => addSkill(skill)}
                className="text-[11px] font-semibold px-2.5 py-1 rounded-xl bg-slate-100 text-slate-700 hover:bg-indigo-50 hover:text-indigo-600 border border-slate-200/60 transition cursor-pointer"
              >
                + {skill}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // ── Step 5: Projects ───────────────────────────────────────────────────────
  if (step === 5) {
    const addProject = () => {
      setData({
        ...data,
        projects: [
          ...(data.projects || []),
          { name: "", techStack: "", github: "", description: "" },
        ],
      });
    };

    const updateProject = (index, field, value) => {
      const updated = data.projects.map((proj, i) =>
        i === index ? { ...proj, [field]: value } : proj
      );
      setData({ ...data, projects: updated });
    };

    const removeProject = (index) => {
      setData({ ...data, projects: data.projects.filter((_, i) => i !== index) });
    };

    return (
      <div className="space-y-4">
        {(data.projects || []).length === 0 && (
          <div className="text-center py-6 text-slate-400 space-y-1">
            <p className="text-xs font-semibold">No projects added yet.</p>
            <p className="text-[11px]">Projects are high-impact for freshers to stand out in screening.</p>
          </div>
        )}

        {(data.projects || []).map((proj, index) => (
          <EntryCard
            key={index}
            title={`Project #${index + 1}`}
            onRemove={() => removeProject(index)}
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <FormInput
                label="Project Title"
                value={proj.name}
                onChange={(v) => updateProject(index, "name", v)}
                placeholder="Fresher.AI Platform"
              />
              <FormInput
                label="Tech Stack Used"
                value={proj.techStack}
                onChange={(v) => updateProject(index, "techStack", v)}
                placeholder="React, FastAPI, Groq LLM, Supabase"
              />
            </div>
            <FormInput
              label="GitHub Repository / Live Demo URL"
              value={proj.github}
              onChange={(v) => updateProject(index, "github", v)}
              placeholder="https://github.com/rahul/fresherai"
            />
            <FormTextarea
              label="Key Features & Technical Accomplishments"
              value={proj.description}
              onChange={(v) => updateProject(index, "description", v)}
              placeholder="• Architected full-stack career platform serving AI mock interviews and ATS scoring&#10;• Implemented real-time LangGraph multi-agent interview evaluator"
              rows={4}
            />
          </EntryCard>
        ))}

        <button
          type="button"
          onClick={addProject}
          className="w-full py-3 rounded-2xl border-2 border-dashed border-slate-200 hover:border-indigo-400 text-slate-600 hover:text-indigo-600 font-bold text-xs flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
        >
          <FiPlus size={15} />
          <span>Add Project</span>
        </button>
      </div>
    );
  }

  // ── Step 6: Summary ────────────────────────────────────────────────────────
  if (step === 6) {
    return (
      <div className="space-y-4">
        <FormTextarea
          label="Professional Executive Summary"
          value={data.summary}
          onChange={(v) => setData({ ...data, summary: v })}
          placeholder="Passionate and results-driven Software Engineer with hands-on expertise in building full-stack web applications using React, Python FastAPI, and PostgreSQL. Proficient in Data Structures, Algorithms, and scalable REST API architectures."
          rows={6}
        />
        <p className="text-[11px] text-slate-400 leading-relaxed">
          💡 <strong>Tip:</strong> Keep your summary between 2 to 4 impactful sentences. Focus on your strongest tech stack and career passion.
        </p>
      </div>
    );
  }

  return null;
}